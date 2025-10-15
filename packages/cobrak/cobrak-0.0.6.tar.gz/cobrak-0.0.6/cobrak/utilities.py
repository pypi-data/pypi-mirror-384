"""General utility functions for COBRAk dataclasses and more.

This module does not include I/O functions which are found in COBRAk's "io" module.
"""

# IMPORT SECTION #
import operator
import os
from copy import deepcopy
from random import choice
from statistics import mean, median
from typing import Any, TypeVar

import numpy as np
from numpy import array, exp, percentile
from numpy.random import uniform
from pydantic import (
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    conint,
    validate_call,
)
from pyomo.environ import ConcreteModel, Var, log
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.opt.results import SolverResults
from scipy.linalg import null_space
from sympy import Matrix

from .bigg_metabolites_functionality import bigg_parse_metabolites_file
from .constants import (
    ALL_OK_KEY,
    ALPHA_VAR_PREFIX,
    DF_VAR_PREFIX,
    DG0_VAR_PREFIX,
    ENZYME_VAR_INFIX,
    ENZYME_VAR_PREFIX,
    ERROR_BOUND_LOWER_CHANGE_PREFIX,
    ERROR_BOUND_UPPER_CHANGE_PREFIX,
    ERROR_VAR_PREFIX,
    GAMMA_VAR_PREFIX,
    IOTA_VAR_PREFIX,
    KAPPA_VAR_PREFIX,
    LNCONC_VAR_PREFIX,
    OBJECTIVE_VAR_NAME,
    REAC_ENZ_SEPARATOR,
    REAC_FWD_SUFFIX,
    REAC_REV_SUFFIX,
    SOLVER_STATUS_KEY,
    TERMINATION_CONDITION_KEY,
    Z_VAR_PREFIX,
)
from .dataclasses import (
    CorrectionConfig,
    Enzyme,
    EnzymeReactionData,
    ExtraLinearConstraint,
    Model,
    Reaction,
)
from .io import get_files, json_write, standardize_folder
from .ncbi_taxonomy_functionality import parse_ncbi_taxonomy
from .pyomo_functionality import get_model_var_names

# GENERICS DEFINITIONS #
T = TypeVar("T")  # Not neccessary anymore as soon as Python >= 3.12 can be used
U = TypeVar("U")  # Not neccessary anymore as soon as Python >= 3.12 can be used


# "PRIVATE" FUNCTIONS SECTION #
@validate_call(validate_return=True)
def _compare_two_results_with_statistics(
    cobrak_model: Model,
    result_1: dict[str, float],
    result_2: dict[str, float],
    min_reac_flux: NonNegativeFloat,
) -> tuple[dict[str, float], dict[int, list[str]]]:
    """Compares two optimization results and calculates statistics on the absolute flux differences.

    This function uses the `compare_optimization_result_fluxes` function to compare the fluxes of the two optimization results.
    The absolute flux differences are then calculated and used to compute the statistics.

    Args:
        cobrak_model (Model): The COBRA-k model used for the optimization.
        result_1 (dict[str, float]): The first optimization result.
        result_2 (dict[str, float]): The second optimization result.
        min_reac_flux (float): The minimum reaction flux.

    Returns:
        tuple[dict[str, float], dict[int, list[str]]]: A tuple containing two dictionaries.
        The first dictionary contains statistics on the absolute flux differences, including:
        - "min": The minimum absolute flux difference.
        - "max": The maximum absolute flux difference.
        - "sum": The sum of all absolute flux differences.
        - "mean": The mean of all absolute flux differences.
        - "median": The median of all absolute flux differences.
        The second dictionary contains lists of reaction IDs, where:
        - Key 0: Reactions where result_1 has a higher flux.
        - Key 1: Reactions where result_2 has a higher flux.
    """
    flux_comparison = compare_optimization_result_fluxes(
        cobrak_model, result_1, result_2, min_reac_flux
    )
    abs_flux_differences = [x[0] for x in flux_comparison.values()]

    return (
        {
            "min": min(abs_flux_differences),
            "max": max(abs_flux_differences),
            "sum": sum(abs_flux_differences),
            "mean": mean(abs_flux_differences),
            "median": median(abs_flux_differences),
        },
        {
            0: [
                reac_id
                for reac_id in flux_comparison
                if flux_comparison[reac_id][1] == 1
            ],
            1: [
                reac_id
                for reac_id in flux_comparison
                if flux_comparison[reac_id][1] == 2
            ],
        },
    )


# "PUBLIC" FUNCTIONS SECTION #
@validate_call(validate_return=True)
def add_objective_value_as_extra_linear_constraint(
    cobrak_model: Model,
    objective_value: float,
    objective_target: str | dict[str, float],
    objective_sense: int,
) -> Model:
    """Adds a linear constraint to a COBRA-k model that enforces the objective value.

    This function creates an extra linear constraint that limits the objective
    value to be within a small range around the original objective value. This
    can be useful for enforcing constraints during model manipulation or
    optimization.

    Args:
        cobrak_model: The COBRA-k Model object to be modified.
        objective_value: The original objective value.
        objective_target: A string representing the objective variable or a dictionary
            mapping variables to their coefficients in the objective function.
        objective_sense: The sense of the objective function (1 for maximization, -1 for minimization).

    Returns:
        The modified COBRA-k Model object with the extra linear constraint added.
    """
    if is_objsense_maximization(objective_sense):
        lower_value = objective_value - 1e-12
        upper_value = None
    else:
        lower_value = None
        upper_value = objective_value + 1e-12

    if type(objective_target) is str:
        objective_target = {objective_target: 1.0}
    cobrak_model.extra_linear_constraints = [
        ExtraLinearConstraint(
            stoichiometries=objective_target,
            lower_value=lower_value,
            upper_value=upper_value,
        )
    ]
    return cobrak_model


def add_statuses_to_optimziation_dict(
    optimization_dict: dict[str, float], pyomo_results: SolverResults
) -> dict[str, float]:
    """Adds solver statuses to the optimization dict.

    This includes:
    * SOLVER_STATUS_KEY's value, which is 0 for ok, 1 for warning
       and higher values for problems.
    * TERMINATION_CONDITION_KEY's value, which is 0.1 for globally optimal,
      0.2 for optimal, 0.3 for locally optimal and >=1 for any result with problems.
    * ALL_OK_KEY's value, which is True if SOLVER_STATUS_KEY's value < 0
      and TERMINATION_CONDITION_KEY's value < 1.

    Args:
        optimization_dict (dict[str, float]): The optimization dict
        pyomo_results (SolverResults): The pyomo results object

    Raises:
        ValueError: Unknown pyomo_results.solver.status or termination_condition

    Returns:
        dict[str, float]: The pyomo results dict with the added statuses.
    """
    solver_status = get_solver_status_from_pyomo_results(pyomo_results)

    termination_condition = get_termination_condition_from_pyomo_results(pyomo_results)

    optimization_dict[SOLVER_STATUS_KEY] = solver_status
    optimization_dict[TERMINATION_CONDITION_KEY] = termination_condition
    optimization_dict[ALL_OK_KEY] = (
        termination_condition >= 0 and termination_condition < 1
    ) and (solver_status == 0)

    return optimization_dict


@validate_call(validate_return=True)
def apply_error_correction_on_model(
    cobrak_model: Model,
    correction_result: dict[str, float],
    min_abs_error_value: NonNegativeFloat = 0.01,
    min_rel_error_value: NonNegativeFloat = 0.01,
    verbose: bool = False,
) -> Model:
    """Applies error corrections to a COBRAl model based on a correction result dictionary.

    This function iterates through the `correction_result` dictionary and applies corrections
    to reaction k_cat values, Michaelis-Menten constants (k_M), Gibbs free energy changes (ΔᵣG'°)
    as well as the inhibition terms (k_I) and activation terms (k_A).
    The corrections are applied only if the (for all parameters except ΔᵣG'°) relative or (for ΔᵣG'°) absolute
    error exceeds specified thresholds.

    Args:
        cobrak_model: The COBRAl model to be corrected.
        correction_result: A dictionary containing error correction values.  Keys are expected to
            contain information about the reaction, metabolite or other variable value being corrected.
        min_abs_error_value: The minimum absolute error value for applying corrections.
        min_rel_error_value: The minimum relative error value for applying corrections.
        verbose: If True, prints details of the corrections being applied.

    Returns:
        A deep copy of the COBRAk model with the error corrections applied.
    """
    changed_model = deepcopy(cobrak_model)
    error_entries = {
        key: value
        for key, value in correction_result.items()
        if key.startswith(ERROR_VAR_PREFIX)
    }
    for key, value in error_entries.items():
        if "_kcat_times_e_" in key:
            reac_id = key.split("_kcat_times_e_")[1]
            enzyme_id = get_reaction_enzyme_var_id(
                reac_id, cobrak_model.reactions[reac_id]
            )
            k_cat = cobrak_model.reactions[reac_id].enzyme_reaction_data.k_cat
            enzyme_conc = correction_result[enzyme_id]
            e_times_kcat = k_cat * enzyme_conc
            if e_times_kcat == 0.0:
                continue
            kcat_correction = (e_times_kcat + value) / e_times_kcat
            if (kcat_correction - 1.0) < min_rel_error_value:
                continue
            changed_model.reactions[
                reac_id
            ].enzyme_reaction_data.k_cat *= kcat_correction
            if verbose:
                print(
                    f"Correct kcat of {reac_id} from {k_cat} to {changed_model.reactions[reac_id].enzyme_reaction_data.k_cat}"
                )
        elif key.endswith(("_substrate", "_product")):
            reac_id = key.split("____")[0].replace(ERROR_VAR_PREFIX + "_", "")
            met_id = (
                key.split("____")[1].replace("_substrate", "").replace("_product", "")
            )
            original_km = cobrak_model.reactions[reac_id].enzyme_reaction_data.k_ms[
                met_id
            ]
            if key.endswith("_product"):
                new_value = exp(log(original_km) + value)
                if new_value / original_km < (min_rel_error_value + 1.0):
                    continue
                changed_model.reactions[reac_id].enzyme_reaction_data.k_ms[met_id] = (
                    exp(log(original_km) + value)
                )
            else:
                new_value = exp(log(original_km) - value)
                if (original_km / new_value) < (min_rel_error_value + 1.0):
                    continue
                changed_model.reactions[reac_id].enzyme_reaction_data.k_ms[met_id] = (
                    exp(log(original_km) - value)
                )
            if verbose:
                print(
                    f"Correct km of {met_id} in {reac_id} from {original_km} to {changed_model.reactions[reac_id].enzyme_reaction_data.k_ms[met_id]}"
                )
        elif key.endswith("_iota"):
            reac_id = key.split("____")[1]
            met_id = key.split("____")[2]
            original_ki = cobrak_model.reactions[reac_id].enzyme_reaction_data.k_i[
                met_id
            ]
            new_value = exp(log(original_ki) + value)
            if new_value / original_ki < (min_rel_error_value + 1.0):
                continue
            changed_model.reactions[reac_id].enzyme_reaction_data.k_is[met_id] = exp(
                log(original_ki) + value
            )
            if verbose:
                print(
                    f"Correct ki of {met_id} in {reac_id} from {original_ki} to {changed_model.reactions[reac_id].enzyme_reaction_data.k_is[met_id]}"
                )
        elif key.endswith("_alpha"):
            reac_id = key.split("____")[1]
            met_id = key.split("____")[2]
            original_ka = cobrak_model.reactions[reac_id].enzyme_reaction_data.k_a[
                met_id
            ]
            new_value = exp(log(original_ka) + value)
            if new_value / original_ka < (min_rel_error_value + 1.0):
                continue
            changed_model.reactions[reac_id].enzyme_reaction_data.k_as[met_id] = exp(
                log(original_ka) + value
            )
            if verbose:
                print(
                    f"Correct ka of {met_id} in {reac_id} from {original_ka} to {changed_model.reactions[reac_id].enzyme_reaction_data.k_as[met_id]}"
                )
        elif "dG0_" in key:
            if value < min_abs_error_value:
                continue
            reac_id = key.split("dG0_")[1]
            changed_model.reactions[reac_id].dG0 -= value
            if verbose:
                original_dG0 = cobrak_model.reactions[reac_id].dG0
                print(
                    f"Correct ΔG'° {reac_id} from {original_dG0} to {changed_model.reactions[reac_id].dG0}"
                )

    return changed_model


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def apply_variability_dict(
    model: ConcreteModel,
    cobrak_model: Model,  # noqa: ARG001
    variability_dict: dict[str, tuple[float, float]],
    error_scenario: dict[str, tuple[float, float]] = {},
    abs_epsilon: NonNegativeFloat = 1e-5,
) -> ConcreteModel:
    """Applies the variability data as new variable bounds in the pyomo model

    I.e., if the variaility of a variable A is [-10;10],
    A is now set to be -10 <= A <= 10 by changing
    its lower and upper bound.

    Args:
        model (ConcreteModel): The pyomo model
        variability_dict (dict[str, tuple[float, float]]): The variability data
        abs_epsilon (_type_, optional): Under this value, the given value is assumed to be 0.0. Defaults to 1e-9.

    Returns:
        ConcreteModel: The pyomo model with newly set variable bounds
    """
    model_varnames = get_model_var_names(model)
    for var_id, variability in variability_dict.items():
        if var_id in error_scenario:
            continue
        try:
            if abs(variability[0]) < abs_epsilon:
                getattr(model, var_id).setlb(0.0)
            else:
                lbchange_var_id = f"{ERROR_BOUND_LOWER_CHANGE_PREFIX}{var_id}"
                if lbchange_var_id in model_varnames:
                    getattr(model, var_id).setlb(
                        variability[0] - getattr(model, lbchange_var_id).value
                    )
                else:
                    getattr(model, var_id).setlb(variability[0])
            if abs(variability[1]) < abs_epsilon:
                getattr(model, var_id).setub(0.0)
            else:
                ubchange_var_id = f"{ERROR_BOUND_UPPER_CHANGE_PREFIX}{var_id}"
                if ubchange_var_id in model_varnames:
                    getattr(model, var_id).setub(
                        variability[1] + getattr(model, ubchange_var_id).value
                    )
                else:
                    getattr(model, var_id).setub(variability[1])
        except AttributeError:
            pass
    return model


@validate_call(validate_return=True)
def combine_enzyme_reaction_datasets(
    datasets: list[dict[str, EnzymeReactionData | None]],
) -> dict[str, EnzymeReactionData | None]:
    """Combines the enzyme reaction data from the given sources

    The first given dataset has precedence, meaning that its data (k_cats, k_ms, ...)
    will be set first. For any reaction/metabolite where data is missing, it is then looked
    up in the second given dataset, then in the third and so on.

    Args:
        datasets (list[dict[str, EnzymeReactionData  |  None]]): The enzyme reaction datasets

    Returns:
        dict[str, EnzymeReactionData | None]: The combined enzyme reaction data
    """
    combined_data: dict[str, EnzymeReactionData] = {}
    for dataset in datasets:
        for reac_id, enzyme_reaction_data in dataset.items():
            if enzyme_reaction_data is None:
                continue

            if (reac_id not in combined_data) or (
                combined_data[reac_id].k_cat_references[0].tax_distance
                > enzyme_reaction_data.k_cat_references[0].tax_distance
            ):
                combined_data[reac_id] = EnzymeReactionData(
                    identifiers=enzyme_reaction_data.identifiers,
                    k_cat=enzyme_reaction_data.k_cat,
                    k_cat_references=enzyme_reaction_data.k_cat_references,
                )

            for met_id, k_m in enzyme_reaction_data.k_ms.items():
                if met_id not in combined_data[reac_id].k_ms or (
                    combined_data[reac_id].k_m_references[met_id][0].tax_distance
                    > enzyme_reaction_data.k_m_references[met_id][0].tax_distance
                ):
                    combined_data[reac_id].k_ms[met_id] = k_m
                    combined_data[reac_id].k_m_references[met_id] = (
                        enzyme_reaction_data.k_m_references[met_id]
                    )

            for met_id, k_i in enzyme_reaction_data.k_is.items():
                if met_id not in combined_data[reac_id].k_is or (
                    combined_data[reac_id].k_i_references[met_id][0].tax_distance
                    > enzyme_reaction_data.k_i_references[met_id][0].tax_distance
                ):
                    combined_data[reac_id].k_is[met_id] = k_i
                    combined_data[reac_id].k_i_references[met_id] = (
                        enzyme_reaction_data.k_i_references[met_id]
                    )

            for met_id, k_a in enzyme_reaction_data.k_as.items():
                if met_id not in combined_data[reac_id].k_as or (
                    combined_data[reac_id].k_a_references[met_id][0].tax_distance
                    > enzyme_reaction_data.k_a_references[met_id][0].tax_distance
                ):
                    combined_data[reac_id].k_as[met_id] = k_a
                    combined_data[reac_id].k_a_references[met_id] = (
                        enzyme_reaction_data.k_a_references[met_id]
                    )

            hills = enzyme_reaction_data.hill_coefficients
            for met_id in hills.kappa:
                if met_id not in combined_data[reac_id].hill_coefficients.kappa or (
                    combined_data[reac_id]
                    .hill_coefficient_references.kappa[met_id][0]
                    .tax_distance
                    > enzyme_reaction_data.hill_coefficient_references.kappa[met_id][
                        0
                    ].tax_distance
                ):
                    combined_data[reac_id].hill_coefficients.kappa[met_id] = (
                        hills.kappa[met_id]
                    )
                    combined_data[reac_id].hill_coefficient_references.kappa[met_id] = (
                        enzyme_reaction_data.hill_coefficient_references.kappa[met_id]
                    )
            for met_id in hills.iota:
                if met_id not in combined_data[reac_id].hill_coefficients.iota or (
                    combined_data[reac_id]
                    .hill_coefficient_references.iota[met_id][0]
                    .tax_distance
                    > enzyme_reaction_data.hill_coefficient_references.iota[met_id][
                        0
                    ].tax_distance
                ):
                    combined_data[reac_id].hill_coefficients.iota[met_id] = hills.iota[
                        met_id
                    ]
                    combined_data[reac_id].hill_coefficient_references.iota[met_id] = (
                        enzyme_reaction_data.hill_coefficient_references.iota[met_id]
                    )
            for met_id in hills.alpha:
                if met_id not in combined_data[reac_id].hill_coefficients.alpha or (
                    combined_data[reac_id]
                    .hill_coefficient_references.alpha[met_id][0]
                    .tax_distance
                    > enzyme_reaction_data.hill_coefficient_references.alpha[met_id][
                        0
                    ].tax_distance
                ):
                    combined_data[reac_id].hill_coefficients.alpha[met_id] = (
                        hills.alpha[met_id]
                    )
                    combined_data[reac_id].hill_coefficient_references.alpha[met_id] = (
                        enzyme_reaction_data.hill_coefficient_references.alpha[met_id]
                    )

    return combined_data


@validate_call(validate_return=True)
def compare_optimization_result_reaction_uses(
    cobrak_model: Model,
    results: list[dict[str, float]],
    min_abs_flux: NonNegativeFloat = 1e-6,
) -> None:
    """Compares the usage of reactions across multiple optimization (e.g. FBA) results.

    This function analyzes the frequency of reaction usage in a set of optimization results
    from a COBRAk Model. It identifies which reactions are used in each solution and prints
    the number of solutions in which each reaction is active, considering a minimum absolute
    flux threshold.

    Parameters:
    - cobrak_model (Model): The COBRAk model containing the reactions to be analyzed.
    - results (list[dict[str, float]]): A list of dictionaries, each representing an optimization
      result with reaction IDs as keys and their corresponding flux values as values.
    - min_abs_flux (float, optional): The minimum absolute flux value to consider a reaction as used.
      Reactions with absolute flux values below this threshold are ignored. Defaults to 1e-6.

    Returns:
    - None: This function does not return a value. It prints the number of solutions in which each
      reaction is used, grouped by the number of solutions.
    """
    results = deepcopy(results)
    results = [
        get_base_id_optimzation_result(
            cobrak_model,
            result,
        )
        for result in results
    ]

    reac_ids: list[str] = [
        get_base_id(
            reac_id,
            cobrak_model.fwd_suffix,
            cobrak_model.rev_suffix,
            cobrak_model.reac_enz_separator,
        )
        for reac_id in cobrak_model.reactions
    ]
    reacs_to_uses: dict[str, list[int]] = {reac_id: [] for reac_id in reac_ids}
    for num, result in enumerate(results):
        for reac_id in reac_ids:
            if reac_id not in result:
                continue
            if abs(result[reac_id]) <= min_abs_flux:
                continue
            if num in reacs_to_uses[reac_id]:
                continue
            reacs_to_uses[reac_id].append(num)
    min_num_results = min(len(i) for i in reacs_to_uses.values())
    max_num_results = max(len(i) for i in reacs_to_uses.values())
    print(min_num_results, max_num_results)
    for num_results in range(min_num_results, max_num_results + 1):
        print(f"Reactions used in {num_results} solutions:")
        print(
            [
                (reac_id, uses)
                for reac_id, uses in reacs_to_uses.items()
                if len(uses) == num_results
            ]
        )
        print("===")


@validate_call(validate_return=True)
def compare_optimization_result_fluxes(
    cobrak_model: Model,
    result_1: dict[str, float],
    result_2: dict[str, float],
    min_reac_flux: float = 1e-8,
) -> dict[str, tuple[float, int]]:
    """Compares the fluxes of two optimization results and returns a dictionary with the absolute differences and indicators of which result has a higher flux.

    This function first corrects the fluxes of the two results by considering the forward and reverse reactions.
    It then calculates the absolute differences between the corrected fluxes and determines which result has a higher flux for each reaction.
    Reactions with fluxes below the minimum reaction flux threshold are ignored.

    Args:
    cobrak_model (Model): The COBRA-k model used for the optimization.
    result_1 (dict[str, float]): The first optimization result.
    result_2 (dict[str, float]): The second optimization result.
    min_reac_flux (float, optional): The minimum reaction flux to consider. Defaults to 1e-8.

    Returns:
    dict[str, tuple[float, int]]: A dictionary where each key is a reaction ID and each value is a tuple containing:
    - The absolute difference between the fluxes of the two results.
    - An indicator of which result has a higher flux:
    - 0: Both results have the same flux.
    - 1: The first result has a higher flux.
    - 2: The second result has a higher flux.
    """
    corrected_result_1: dict[str, float] = {}
    corrected_result_2: dict[str, float] = {}
    for result, corrected_result in [
        (result_1, corrected_result_1),
        (result_2, corrected_result_2),
    ]:
        for var_id in result:
            if var_id not in cobrak_model.reactions:
                continue
            flux = get_fwd_rev_corrected_flux(
                var_id,
                list(result.keys()),
                result,
                cobrak_model.fwd_suffix,
                cobrak_model.rev_suffix,
            )
            if flux >= min_reac_flux:
                corrected_result[var_id] = flux

    abs_results = {}
    for reac_id in cobrak_model.reactions:
        if (reac_id in corrected_result_1) and (reac_id in corrected_result_2):
            flux_1, flux_2 = corrected_result_1[reac_id], corrected_result_2[reac_id]
            # if other_id not in abs_results:
            abs_results[reac_id] = (abs(flux_1 - flux_2), 0)
        elif reac_id in corrected_result_1:
            flux_1 = corrected_result_1[reac_id]
            # if other_id not in abs_results:
            abs_results[reac_id] = (flux_1, 1)
        elif reac_id in corrected_result_2:
            flux_2 = corrected_result_2[reac_id]
            # if other_id not in abs_results:
            abs_results[reac_id] = (flux_2, 2)

    return abs_results


@validate_call(validate_return=True)
def compare_multiple_results_to_best(
    cobrak_model: Model,
    results: list[dict[str, float]],
    is_maximization: bool,
    min_reac_flux: float = 1e-8,
) -> dict[int, tuple[dict[str, float], dict[int, list[str]]]]:
    """Compares multiple optimization results to the best result and returns a dictionary with statistics and comparisons.

    This function first identifies the best result based on the objective value.
    It then compares each result to the best result and calculates statistics and comparisons.
    The comparisons include the difference between the objective values and the reaction fluxes.
    Reactions with fluxes below the minimum reaction flux threshold are ignored.

    Args:
    cobrak_model (Model): The COBRA-k model used for the optimization.
    results (list[dict[str, float]]): A list of optimization results.
    is_maximization (bool): Whether the optimization is a maximization problem.
    min_reac_flux (float, optional): The minimum reaction flux to consider. Defaults to 1e-8.

    Returns:
    dict[int, tuple[dict[str, float], dict[int, list[str]]]]: A dictionary where each key is the index of a result and each value is a tuple containing:
    - A dictionary with reaction statistics, including:
    - "min": The minimum absolute flux difference.
    - "max": The maximum absolute flux difference.
    - "sum": The sum of all absolute flux differences.
    - "mean": The mean of all absolute flux differences.
    - "median": The median of all absolute flux differences.
    - "obj_difference": The difference between the objective value of the current result and the best result.
    - A dictionary with reaction comparisons, where each key is an integer indicating which result has a higher flux:
    - 0: The best result has a higher flux.
    - 1: The current result has a higher flux.
    """
    objective_values = [x[OBJECTIVE_VAR_NAME] for x in results]
    best_objective = max(objective_values) if is_maximization else min(objective_values)
    best_idx = objective_values.index(best_objective)

    comparisons: dict[int, tuple[dict[str, float], dict[int, list[str]]]] = {}
    for idx in range(len(results)):
        if idx == best_idx:
            continue
        obj_difference = (
            objective_values[idx] - best_objective
            if is_maximization
            else best_objective - objective_values[idx]
        )
        reac_statistics, reac_comparisons = _compare_two_results_with_statistics(
            cobrak_model,
            results[idx],
            results[best_idx],
            min_reac_flux,
        )
        reac_statistics["obj_difference"] = obj_difference
        comparisons[idx] = (reac_statistics, reac_comparisons)

    return comparisons


@validate_call(validate_return=True)
def count_last_equal_elements(lst: list[Any]) -> int:
    """Counts the number of consecutive equal elements from the end of the list.

    Parameters:
    lst (list[Any]): A Python list.

    Returns:
    int: The number of consecutive equal elements from the end of the list.

    Examples:
    >>> count_last_equal_elements([1.0, 2.0, 1.0, 3.0, 3.0, 3.0])
    3
    >>> count_last_equal_elements([1.0, 2.0, 2.0, 1.0])
    1
    >>> count_last_equal_elements([1.0, 1.0, 1.0, 1.0])
    4
    >>> count_last_equal_elements([])
    0
    """
    if not lst:
        return 0  # Return 0 if the list is empty

    count = 1  # Start with the last element
    last_element = lst[-1]

    # Iterate from the second last element to the beginning
    for i in range(len(lst) - 2, -1, -1):
        if lst[i] == last_element:
            count += 1
        else:
            break  # Stop counting when a different element is found

    return count


@validate_call(validate_return=True)
def create_cnapy_scenario_out_of_optimization_dict(
    path: str,
    cobrak_model: Model,
    optimization_dict: dict[str, float],
    desplit_reactions: bool = True,
) -> None:
    """Create a CNApy scenario file from an optimization dictionary and a COBRAk Model.

    Args:
        path (str): The file path where the CNApy scenario will be saved.
        cobrak_model (Model): The COBRAk Model.
        optimization_dict (dict[str, float]): An optimization result dict.
        desplit_reactions: bool: Whether or not the fluxes of split reversible reaction
                                 shall be recombined. Defaults to True.

    Returns:
        None: The function saves the CNApy scenario to the specified path.
    """
    base_id_result = (
        get_base_id_optimzation_result(
            cobrak_model,
            optimization_dict,
        )
        if desplit_reactions
        else optimization_dict
    )
    cnapy_scenario: dict[str, tuple[float, float]] = {
        key: (value, value) for key, value in base_id_result.items()
    }
    json_write(path, cnapy_scenario)


@validate_call(validate_return=True)
def create_cnapy_scenario_out_of_variability_dict(
    path: str,
    cobrak_model: Model,
    variability_dict: dict[str, tuple[float, float]],
    desplit_reactions: bool = True,
) -> None:
    """Create a CNApy scenario file from a variability dictionary and a COBRAk model.

    Args:
        path (str): The file path where the CNApy scenario file will be saved.
        cobrak_model (Model): The COBRA-k model containing reactions.
        variability_dict (dict[str, list[float]]): A dictionary mapping reaction IDs to their minimum and maximum flux values.
        desplit_reactions: bool: Whether or not the fluxes of split reversible reaction
                                 shall be recombined. Defaults to True.
    Returns:
        None: The function saves the CNApy scenario to the specified path.
    """
    cnapy_scenario: dict[str, list[float]] = {}

    for reac_id in cobrak_model.reactions:
        if reac_id not in variability_dict:
            continue
        base_id = (
            get_base_id(
                reac_id,
                cobrak_model.fwd_suffix,
                cobrak_model.rev_suffix,
                cobrak_model.reac_enz_separator,
            )
            if desplit_reactions
            else reac_id
        )

        multiplier = 1 if reac_id.endswith(cobrak_model.fwd_suffix) else -1
        min_flux = variability_dict[reac_id][0]
        max_flux = variability_dict[reac_id][0]

        if base_id not in cnapy_scenario:
            cnapy_scenario[base_id] = [0.0, 0.0]

        cnapy_scenario[base_id][0] += multiplier * min_flux
        cnapy_scenario[base_id][1] += multiplier * max_flux

    json_write(path, cnapy_scenario)


@validate_call(validate_return=True)
def delete_orphaned_metabolites_and_enzymes(cobrak_model: Model) -> Model:
    """Removes orphaned metabolites and enzymes from a COBRAk model.

    This function cleans up a COBRAk model by deleting metabolites and enzymes that are not used
    in any reactions. A metabolite is considered orphaned if it does not appear in the stoichiometries
    of any reactions. Similarly, an enzyme is considered orphaned if it is not associated with any
    enzyme reaction data in the model's reactions.

    Parameters:
    - cobrak_model (Model): The COBRAk model to be cleaned. This model contains reactions,
      metabolites, and enzymes that may include unused entries.

    Returns:
    - Model: The cleaned COBRAk model with orphaned metabolites and enzymes removed.
    """
    used_metabolites = []
    used_enzyme_ids = []
    for reaction in cobrak_model.reactions.values():
        used_metabolites += list(reaction.stoichiometries.keys())

        if reaction.enzyme_reaction_data is not None:
            used_enzyme_ids += reaction.enzyme_reaction_data.identifiers

    # Delete metabolites
    mets_to_delete = [
        met_id for met_id in cobrak_model.metabolites if met_id not in used_metabolites
    ]
    for met_to_delete in mets_to_delete:
        del cobrak_model.metabolites[met_to_delete]

    # Delete enzymes
    enzymes_to_delete = [
        enzyme_id
        for enzyme_id in cobrak_model.enzymes
        if enzyme_id not in used_enzyme_ids
    ]
    for enzyme_to_delete in enzymes_to_delete:
        del cobrak_model.enzymes[enzyme_to_delete]

    return cobrak_model


@validate_call(validate_return=True)
def delete_unused_reactions_in_optimization_dict(
    cobrak_model: Model,
    optimization_dict: dict[str, float],
    exception_prefix: str = "",
    delete_missing_reactions: bool = True,
    min_abs_flux: NonNegativeFloat = 1e-15,
    do_not_delete_with_z_var_one: bool = True,
) -> Model:
    """Delete unused reactions in a COBRAk model based on an optimization dictionary.

    This function creates a deep copy of the provided COBRAk model and removes reactions that are either not present
    in the optimization dictionary or have flux values below a specified threshold. Optionally,
    reactions with a specific prefix can be excluded from deletion.
    Additionally, orphaned metabolites (those not used in any remaining reactions) are also removed.

    Args:
        cobrak_model (Model): COBRAk model containing reactions and metabolites.
        optimization_dict (dict[str, float]): Dictionary mapping reaction IDs to their optimized flux values.
        exception_prefix (str, optional): A prefix for reaction IDs that should not be deleted. Defaults to "".
        delete_missing_reactions (bool, optional): Whether to delete reactions not present in the optimization dictionary. Defaults to True.
        min_abs_flux (float, optional): The minimum absolute flux value below which reactions are considered unused. Defaults to 1e-10.

    Returns:
        Model: A new COBRAk model with unused reactions and orphaned metabolites removed.
    """
    cobrak_model = deepcopy(cobrak_model)
    reacs_to_delete: list[str] = []
    for reac_id in cobrak_model.reactions:
        to_delete = False
        if (reac_id not in optimization_dict) and delete_missing_reactions:
            to_delete = True
        elif (reac_id in optimization_dict) and abs(
            optimization_dict[reac_id]
        ) <= min_abs_flux:
            z_var_id = f"{Z_VAR_PREFIX}{reac_id}"
            if z_var_id in optimization_dict:
                if do_not_delete_with_z_var_one and (
                    optimization_dict[z_var_id] <= 1e-6
                ):
                    to_delete = True
                else:
                    to_delete = True
            else:
                to_delete = True
        if to_delete:
            reacs_to_delete.append(reac_id)
    for reac_to_delete in reacs_to_delete:
        if (exception_prefix) and (reac_to_delete.startswith(exception_prefix)):
            continue
        del cobrak_model.reactions[reac_to_delete]
    return delete_orphaned_metabolites_and_enzymes(cobrak_model)


@validate_call(validate_return=True)
def delete_unused_reactions_in_variability_dict(
    cobrak_model: Model,
    variability_dict: dict[str, tuple[float, float]],
    extra_reacs_to_delete: list[str] = [],
) -> Model:
    """Delete unused reactions in a COBRAk model based on a variability dictionary.

    This function creates a deep copy of the provided COBRA-k model and removes reactions that have both minimum and maximum flux values
    equal to zero, as indicated in the variability dictionary.
    Additionally, any extra reactions specified in the `extra_reacs_to_delete` list are also removed.
    Orphaned metabolites (those not used in any remaining reactions) are subsequently deleted, too.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and metabolites.
        variability_dict (dict[str, tuple[float, float]]): A dictionary mapping reaction IDs to their minimum and maximum flux values.
        extra_reacs_to_delete (list[str], optional): A list of additional reaction IDs to be deleted. Defaults to an empty list.

    Returns:
        Model: A new COBRAk model with unused reactions and orphaned metabolites removed.
    """
    cobrak_model = deepcopy(cobrak_model)
    reacs_to_delete: list[str] = [] + extra_reacs_to_delete
    for reac_id in cobrak_model.reactions:
        if (variability_dict[reac_id][0] == 0.0) and (
            variability_dict[reac_id][1] == 0.0
        ):
            reacs_to_delete.append(reac_id)
    for reac_to_delete in reacs_to_delete:
        del cobrak_model.reactions[reac_to_delete]

    return delete_orphaned_metabolites_and_enzymes(cobrak_model)


@validate_call(validate_return=True)
def get_active_reacs_from_optimization_dict(
    cobrak_model: Model,
    fba_dict: dict[str, float],
) -> list[str]:
    """Get a list of active reactions from an optimization (e.g. FBA (Flux Balance Analysis)) dictionary.

    This function iterates through the reactions in a COBRAk model and identifies those that have a positive flux value in the provided FBA dictionary.
    Only reactions present in the optimization dictionary and with a flux greater than zero are considered active.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions.
        fba_dict (dict[str, float]): A dictionary mapping reaction IDs to their flux values from an optimization.

    Returns:
        list[str]: A list of reaction IDs that are active (i.e., have a positive flux) according to the optimization dictionary.
    """
    active_reacs: list[str] = []
    for reac_id in cobrak_model.reactions:
        if reac_id not in fba_dict:
            continue
        if fba_dict[reac_id] > 0.0:
            active_reacs.append(reac_id)
    return active_reacs


@validate_call(validate_return=True)
def get_base_id(
    reac_id: str,
    fwd_suffix: str = REAC_FWD_SUFFIX,
    rev_suffix: str = REAC_REV_SUFFIX,
    reac_enz_separator: str = REAC_ENZ_SEPARATOR,
) -> str:
    """Extract the base ID from a reaction ID by removing specified suffixes and separators.

    Processes a reaction ID to remove forward and reverse suffixes
    as well as any enzyme separators, to obtain the base reaction ID.

    Args:
        reac_id (str): The reaction ID to be processed.
        fwd_suffix (str, optional): The suffix indicating forward reactions. Defaults to REAC_FWD_SUFFIX.
        rev_suffix (str, optional): The suffix indicating reverse reactions. Defaults to REAC_REV_SUFFIX.
        reac_enz_separator (str, optional): The separator used between reaction and enzyme identifiers. Defaults to REAC_ENZ_SEPARATOR.

    Returns:
        str: The base reaction ID with specified suffixes and separators removed.
    """
    reac_id_split = reac_id.split(reac_enz_separator)
    return (
        (reac_id_split[0] + "\b")
        .replace(f"{fwd_suffix}\b", "")
        .replace(f"{rev_suffix}\b", "")
        .replace("\b", "")
    )


@validate_call(validate_return=True)
def get_base_id_optimzation_result(
    cobrak_model: Model,
    optimization_dict: dict[str, float],
) -> dict[str, float]:
    """Converts an optimization result to a base reaction ID format in a COBRAk model.

    This function processes an optimization result dictionary, which contains reaction IDs with
    their corresponding flux values, and consolidates these fluxes into base reaction IDs. It
    accounts for forward and reverse reaction suffixes to ensure that the net flux for each base
    reaction ID is calculated correctly.

    Parameters:
    - cobrak_model (Model): The COBRAk model containing the reactions to be processed.
    - optimization_dict (dict[str, float]): A dictionary mapping reaction IDs to their flux values
      from an optimization result.

    Returns:
    - dict[str, float]: A dictionary mapping base reaction IDs to their net flux values, consolidating
      forward and reverse reactions.
    """
    base_id_scenario: dict[str, float] = {}

    for reac_id in cobrak_model.reactions:
        if reac_id not in optimization_dict:
            continue
        base_id = get_base_id(
            reac_id,
            cobrak_model.fwd_suffix,
            cobrak_model.rev_suffix,
            cobrak_model.reac_enz_separator,
        )

        multiplier = -1 if reac_id.endswith(cobrak_model.rev_suffix) else +1
        flux = optimization_dict[reac_id]

        if base_id not in base_id_scenario:
            base_id_scenario[base_id] = 0.0

        base_id_scenario[base_id] += multiplier * flux

    return base_id_scenario


@validate_call(validate_return=True)
def get_cobrak_enzyme_reactions_string(cobrak_model: Model, enzyme_id: str) -> str:
    """Get string of reaction IDs associated with a specific enzyme in the COBRAk model.

    This function iterates through the reactions in a COBRAk model and collects the IDs of reaction
    that involve the specified enzyme.
    The collected reaction IDs are then concatenated into a single string, separated by semicolons.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and enzyme data.
        enzyme_id (str): The ID of the enzyme for which associated reactions are to be found.

    Returns:
        str: A semicolon-separated string of reaction IDs that involve the specified enzyme.
    """
    enzyme_reactions = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if reaction.enzyme_reaction_data is None:
            continue
        if enzyme_id in reaction.enzyme_reaction_data.identifiers:
            enzyme_reactions.append(reac_id)
    return "; ".join(enzyme_reactions)


@validate_call(validate_return=True)
def get_elementary_conservation_relations(
    cobrak_model: Model,
) -> str:
    """Calculate and return the elementary conservation relations (ECRs) of a COBRAk model as a string.

    Computes the null space of the stoichiometric matrix of a COBRAk model to determine the elementary conservation relations.
    It then formats these relations into a human-readable string such as "1 ATP * 1 ADP"

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and metabolites.

    Returns:
        str: A string representation of the elementary conservation relations, where each relation is expressed as a linear combination of metabolites.
    """
    # Convert the list of lists to a sympy Matrix
    S_matrix = Matrix(get_stoichiometric_matrix(cobrak_model)).T  # type: ignore

    # Calculate the null space of the stoichiometric matrix
    null_space = S_matrix.nullspace()

    # Convert the null space vectors to a NumPy array
    ECRs = np.array([ns.T.tolist()[0] for ns in null_space], dtype=float)

    ecrs_list = ECRs.tolist()
    met_ids = list(cobrak_model.metabolites)
    conservation_relations = ""
    for current_ecr in range(len(ecrs_list)):
        ecr = ecrs_list[current_ecr]
        for current_met in range(len(met_ids)):
            value = ecr[current_met]
            if value != 0.0:
                conservation_relations += f" {value} * {met_ids[current_met]} "
        conservation_relations += "\n"

    return conservation_relations


@validate_call(validate_return=True)
def get_enzyme_usage_by_protein_pool_fraction(
    cobrak_model: Model,
    result: dict[str, float],
    min_conc: NonNegativeFloat = 1e-12,
    rounding: NonNegativeInt = 5,
) -> dict[NonNegativeFloat, list[str]]:
    """Return enzyme usage as a fraction of the total protein pool in a COBRAk model.

    This function computes the fraction of the total protein pool used by each enzyme based on the given result dictionary.
    It filters out enzymes with concentrations below a specified minimum and groups the reactions by their protein pool fractions.
    The dictionary is sorted, i.e., low fractions occur first and high fractions last as keys.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and enzyme data.
        result (dict[str, float]): A dictionary mapping variable names to their values, typically from an optimization result.
        min_conc (float, optional): The minimum concentration threshold for considering enzyme usage. Defaults to 1e-12.
        rounding (int, optional): The number of decimal places to round the protein pool fractions. Defaults to 5.

    Returns:
        dict[NonNegativeFloat, list[str]]: A dictionary where the keys are protein pool fractions and the values are lists of
                                reaction IDs that use that fraction of the protein pool.
    """
    protein_pool_fractions: dict[float, list[str]] = {}
    for var_name, value in result.items():
        if not var_name.startswith(ENZYME_VAR_PREFIX):
            continue
        reac_id = var_name.split(ENZYME_VAR_INFIX)[-1]
        full_mw = get_full_enzyme_mw(cobrak_model, cobrak_model.reactions[reac_id])
        if value > min_conc:
            protein_pool_fraction = round(
                (full_mw * value) / cobrak_model.max_prot_pool, rounding
            )
        else:
            continue
        if protein_pool_fraction not in protein_pool_fractions:
            protein_pool_fractions[protein_pool_fraction] = []
        protein_pool_fractions[protein_pool_fraction].append(reac_id)

    return dict(sorted(protein_pool_fractions.items()))


@validate_call(validate_return=True)
def get_extra_linear_constraint_string(
    extra_linear_constraint: ExtraLinearConstraint,
) -> str:
    """Returns a string representation of an extra linear constraint.

    The returned format is:
    "lower_value ≤ stoichiometry * var_id + ... ≤ upper_value"

    Args:
        extra_linear_constraint (ExtraLinearConstraint): The extra linear constraint to convert to a string.

    Returns:
        str: A string representation of the extra linear constraint
    """
    string = ""

    if extra_linear_constraint.lower_value is not None:
        string += f"{extra_linear_constraint.lower_value} ≤ "

    for var_id, stoichiometry in sort_dict_keys(
        extra_linear_constraint.stoichiometries
    ).items():
        if stoichiometry > 0:
            printed_stoichiometry = f" + {stoichiometry}"
        else:
            printed_stoichiometry = f" - {abs(stoichiometry)}"
        string += f"{printed_stoichiometry} {var_id}"

    if extra_linear_constraint.upper_value is not None:
        string += f"≤ {extra_linear_constraint.upper_value}"

    return string.lstrip()


@validate_call(validate_return=True)
def get_fwd_rev_corrected_flux(
    reac_id: str,
    usable_reac_ids: list[str] | set[str],
    result: dict[str, float],
    fwd_suffix: str = REAC_FWD_SUFFIX,
    rev_suffix: str = REAC_REV_SUFFIX,
) -> float:
    """Calculates the direction-corrected flux for a reaction, taking into account the flux of its reverse reaction.

    If the reverse reaction exists and its flux is greater than the flux of the forward reaction, the corrected flux is set to 0.0.
    Otherwise, the corrected flux is calculated as the difference between the flux of the forward reaction and the flux of the reverse reaction.
    If the reverse reaction does not exist or is not usable, the corrected flux is set to the flux of the forward reaction.

    Args:
    reac_id (str): The ID of the reaction.
    usable_reac_ids (list[str] | set[str]): A list or set of IDs of reactions that can be used for correction.
    result (dict[str, float]): A dictionary containing the flux values for each reaction.
    fwd_suffix (str, optional): The suffix used to identify forward reactions. Defaults to REAC_FWD_SUFFIX.
    rev_suffix (str, optional): The suffix used to identify reverse reactions. Defaults to REAC_REV_SUFFIX.

    Returns:
    float: The corrected flux value for the reaction.
    """
    other_id = get_reverse_reac_id_if_existing(
        reac_id,
        fwd_suffix,
        rev_suffix,
    )
    if other_id in usable_reac_ids:
        other_flux = result[other_id]
        this_flux = result[reac_id]
        flux = 0.0 if other_flux > this_flux else this_flux - other_flux
    else:
        flux = result[reac_id]

    return flux


@validate_call(validate_return=True)
def get_full_enzyme_id(identifiers: list[str]) -> str:
    """Generate a full enzyme ID by concatenating the list of enzyme identifiers with a specific separator.

    Args:
        identifiers (list[str]): A list of enzyme identifiers.

    Returns:
        str: A single string representing the full enzyme ID, with single identifiers separated by "_AND_".
    """
    return "_AND_".join(identifiers)


@validate_call(validate_return=True)
def get_full_enzyme_mw(cobrak_model: Model, reaction: Reaction) -> float:
    """Calculate the full molecular weight of enzymes (in kDa) involved in a given reaction.

    This function computes the total molecular weight of all enzymes associated with a specified reaction in the COBRAk model.
    If the reaction does not have any enzyme reaction data, a ValueError is raised.

    - If special (i.e. non-1) stoichiometries are provided in the reaction's `enzyme_reaction_data`, they are used to scale the molecular weights accordingly.
    - If no special stoichiometry is provided for an enzyme, a default stoichiometry of 1 is assumed.
    - The function sums up the molecular weights of all enzymes, multiplied by their respective stoichiometries, to compute the total.

    Args:
        cobrak_model (Model): The COBRA-k model containing enzyme data.
        reaction (Reaction): The reaction for which the full enzyme molecular weight is to be calculated.

    Returns:
        float: The total molecular weight of all enzymes involved in the reaction in kDa

    Raises:
        ValueError: If the reaction does not have any enzyme reaction data.
    """
    if reaction.enzyme_reaction_data is None:
        raise ValueError
    full_mw = 0.0
    for identifier in reaction.enzyme_reaction_data.identifiers:
        if identifier in reaction.enzyme_reaction_data.special_stoichiometries:
            stoichiometry = reaction.enzyme_reaction_data.special_stoichiometries[
                identifier
            ]
        else:
            stoichiometry = 1
        full_mw += stoichiometry * cobrak_model.enzymes[identifier].molecular_weight
    return full_mw


@validate_call(validate_return=True)
def get_df_and_efficiency_factors_sorted_lists(
    cobrak_model: Model,
    result: dict[str, float],
    min_flux: NonNegativeFloat = 0.0,
) -> tuple[
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, tuple[float, int]],
]:
    """Extracts and sorts lists of flux values (df) and κ, γ, ι, α values from a result dictionary.

    This function processes a dictionary of results of a COBRA-k optimization
    to extract and sort lists of flux values (df) and κ, γ, ι, α values values. It filters
    these values based on a minimum flux threshold and returns them as sorted dictionaries.
    The function also calculates and returns a dictionary of kappa times gamma values,
    along with a status indicator representing the number of these values present for each reaction.

    Args:
        cobrak_model: The COBRA-k Model object.
        result: A dictionary containing optimization results.  Keys are expected to
            start with prefixes like 'DF_VAR_PREFIX', 'KAPPA_VAR_PREFIX', and 'GAMMA_VAR_PREFIX'.
        min_flux: The minimum flux value to consider when filtering the results.  Values below this
            threshold are excluded.  Defaults to 0.0.

    Returns:
        A tuple containing four dictionaries:
        1. A dictionary of sorted flux values (df) above the minimum flux.
        2. A dictionary of sorted κ values above the minimum flux.
        3. A dictionary of sorted γ values above the minimum flux.
        4. A dictionary of sorted ι values above the minimum flux.
        5. A dictionary of sorted α values above the minimum flux.
        6. A dictionary of sorted κ⋅γ⋅ι⋅α values, along with a status indicator. If, for a reaction,
        one or more of these efficiency factors is missing, the respective factor is assumed to be 1.0
        thus having no effect on the multiplied value.
    """
    dfs: dict[str, float] = {}
    kappas: dict[str, float] = {}
    gammas: dict[str, float] = {}
    iotas: dict[str, float] = {}
    alphas: dict[str, float] = {}
    for var_id, value in result.items():
        if var_id.startswith(DF_VAR_PREFIX):
            reac_id = var_id[len(DF_VAR_PREFIX) :]
            dfs[reac_id] = value
        if var_id.startswith(KAPPA_VAR_PREFIX):
            reac_id = var_id[len(KAPPA_VAR_PREFIX) :]
            kappas[reac_id] = value
        elif var_id.startswith(GAMMA_VAR_PREFIX):
            reac_id = var_id[len(GAMMA_VAR_PREFIX) :]
            gammas[reac_id] = value
        elif var_id.startswith(IOTA_VAR_PREFIX):
            reac_id = var_id[len(IOTA_VAR_PREFIX) :]
            iotas[reac_id] = value
        elif var_id.startswith(ALPHA_VAR_PREFIX):
            reac_id = var_id[len(ALPHA_VAR_PREFIX) :]
            alphas[reac_id] = value

    all_multiplied_dict: dict[str, tuple[float, int]] = {}
    for reac_id in cobrak_model.reactions:
        status = 0
        product = 1.0
        if reac_id in kappas:
            product *= kappas[reac_id]
            status += 1
        if reac_id in gammas:
            product *= gammas[reac_id]
            status += 1
        if reac_id in iotas:
            product *= iotas[reac_id]
            status += 1
        if reac_id in alphas:
            product *= alphas[reac_id]
            status += 1
        all_multiplied_dict[reac_id] = (product, status)

    sorted_df_keys = sorted(dfs, key=lambda k: dfs[k], reverse=False)
    sorted_kappa_keys = sorted(kappas, key=lambda k: kappas[k], reverse=False)
    sorted_gamma_keys = sorted(gammas, key=lambda k: gammas[k], reverse=False)
    sorted_iota_keys = sorted(iotas, key=lambda k: iotas[k], reverse=False)
    sorted_alpha_keys = sorted(alphas, key=lambda k: alphas[k], reverse=False)
    sorted_product_keys = sorted(
        all_multiplied_dict, key=lambda k: all_multiplied_dict[k], reverse=False
    )
    return (
        {key: dfs[key] for key in sorted_df_keys if result[key] > min_flux},
        {key: kappas[key] for key in sorted_kappa_keys if result[key] > min_flux},
        {key: gammas[key] for key in sorted_gamma_keys if result[key] > min_flux},
        {key: iotas[key] for key in sorted_iota_keys if result[key] > min_flux},
        {key: alphas[key] for key in sorted_alpha_keys if result[key] > min_flux},
        {
            key: all_multiplied_dict[key]
            for key in sorted_product_keys
            if key in result and result[key] > min_flux
        },
    )


@validate_call(validate_return=True)
def get_metabolite_consumption_and_production(
    cobrak_model: Model, met_id: str, optimization_dict: dict[str, float]
) -> tuple[float, float]:
    """Calculate the consumption and production rates of a metabolite in a COBRAk model.

    This function computes the total consumption and production of a specified metabolite
    based on the flux values provided in an optimization dictionary.
    It iterates through the reactions in the COBRAk model, checking the stoichiometries to determine the metabolite's
    consumption or production in each reaction.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and metabolites.
        met_id (str): The ID of the metabolite for which consumption and production rates are to be calculated.
        optimization_dict (dict[str, float]): A dictionary mapping reaction IDs to their optimized flux values.

    Returns:
        tuple[float, float]: A tuple containing the total consumption and production rates of the specified metabolite.
    """
    consumption = 0.0
    production = 0.0
    for reac_id, reaction in cobrak_model.reactions.items():
        if reac_id not in optimization_dict:
            continue
        if met_id not in reaction.stoichiometries:
            continue
        stoichiometry = reaction.stoichiometries[met_id]
        if stoichiometry < 0.0:
            consumption += optimization_dict[reac_id] * stoichiometry
        else:
            production += optimization_dict[reac_id] * stoichiometry
    return consumption, production


@validate_call(validate_return=True)
def in_out_fluxes(
    cobrak_model: Model, opt_dict: dict[str, float], met_id: str
) -> tuple[dict[str, float], dict[str, float]]:
    """Return consumption and production fluxes for a metabolite.

    Parameters
    ----------
    cobrak_model : Model
        COBRA-k model instance.
    opt_dict : dict[str, float]
        Reaction‑id → optimal flux (e.g., FBA solution).
    met_id : str
        Metabolite identifier to analyse.

    Returns
    -------
    tuple[dict[str, float], dict[str, float]]
        (cons_dict, prod_dict) where each maps reaction ids to the absolute
        flux contributed to consumption (negative stoichiometry) or production
        (positive stoichiometry) of ``met_id``. All is returned as absolute values.
    """
    cons_dict: dict[str, float] = {}
    prod_dict: dict[str, float] = {}
    for reac_id, reaction in cobrak_model.reactions.items():
        if reac_id not in opt_dict:
            continue
        if met_id not in reaction.stoichiometries:
            continue
        stoichiometry = reaction.stoichiometries[met_id]
        reac_flux = opt_dict[reac_id]
        if stoichiometry < 0:
            cons_dict.append(abs(stoichiometry) * reac_flux)
        else:
            prod_dict.append(stoichiometry * reac_flux)
    return cons_dict, prod_dict


@validate_call(validate_return=True)
def get_sorted_model_kcats(cobrak_model: Model) -> list[tuple[str, float]]:
    """Extracts k_cat values from reactions with enzyme data in the model, in ascending order
       together with the associated reaction ID.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions with enzyme data.

    Returns:
        list[tuple[str, float]]: A list of (reac_id, k_cat) values for reactions with available enzyme data.
    """
    kcats = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if reaction.enzyme_reaction_data is not None:
            kcats.append((reac_id, reaction.enzyme_reaction_data.k_cat))
    return sorted(kcats, key=operator.itemgetter(1))


@validate_call(validate_return=True)
def get_model_kcats(cobrak_model: Model) -> list[float]:
    """Extracts k_cat values from reactions with enzyme data in the model.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions with enzyme data.

    Returns:
        list[float]: A list of k_cat values for reactions with available enzyme data.
    """
    return [x[1] for x in get_sorted_model_kcats(cobrak_model)]


@validate_call(validate_return=True)
def get_sorted_model_dG0s(
    cobrak_model: Model, abs_values: bool = False, exclude_bw_reacs: bool = True
) -> list[tuple[str, float]]:
    """Extracts standard Gibbs free energy changes (dG0) from reactions in the model and returns them,
       with reaction IDs, in ascending order.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions with thermodynamic data.
        abs_values (bool, optional): If True, returns absolute values of dG0. Defaults to False.

    Returns:
        list[tuple[str, float]]: A list of (reac_id, dG0) values, possibly as absolute values if specified.
    """
    dG0s = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if exclude_bw_reacs and reac_id.endswith(cobrak_model.rev_suffix):
            continue
        if reaction.dG0 is not None:
            dG0s.append(
                (reac_id, abs(reaction.dG0)) if abs_values else (reac_id, reaction.dG0)
            )
    return sorted(dG0s, key=operator.itemgetter(1))


@validate_call(validate_return=True)
def get_model_dG0s(
    cobrak_model: Model, abs_values: bool = False, exclude_bw_reacs: bool = True
) -> list[float]:
    """Extracts standard Gibbs free energy changes (dG0) from reactions in the model.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions with thermodynamic data.
        abs_values (bool, optional): If True, returns absolute values of dG0. Defaults to False.

    Returns:
        list[float]: A list of dG0 values, possibly as absolute values if specified.
    """
    return [
        x[1] for x in get_sorted_model_dG0s(cobrak_model, abs_values, exclude_bw_reacs)
    ]


@validate_call(validate_return=True)
def get_model_kms(
    cobrak_model: Model, return_only_values_with_reference: bool = False
) -> list[float]:
    """Extracts k_m values from reactions with enzyme data in the model.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions with enzyme data.

    Returns:
        list[float]: A flat list of k_m values from all reactions with available enzyme data.
    """
    substrate_kms, product_kms = get_model_kms_by_usage(
        cobrak_model, return_only_values_with_reference
    )
    return substrate_kms + product_kms


@validate_call(validate_return=True)
def get_model_kms_by_usage(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> tuple[list[PositiveFloat], list[PositiveFloat]]:
    """Collects k_M values from a COBRA-k model, separating them into substrate and product lists.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_M values associated with each metabolite. It distinguishes between substrates
    (metabolites with negative stoichiometry) and products (metabolites with positive
    stoichiometry) and separates the corresponding Kms values into two lists.

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A tuple containing two lists: the first list contains k_M values for substrates,
        and the second list contains k_M values for products.
    """
    substrate_kms, product_kms = get_sorted_model_kms_by_usage(
        cobrak_model=cobrak_model,
        return_only_values_with_reference=return_only_values_with_reference,
    )
    return [x[2] for x in substrate_kms], [x[2] for x in product_kms]


@validate_call(validate_return=True)
def get_sorted_model_kms_by_usage(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> tuple[list[tuple[str, str, PositiveFloat]], list[tuple[str, str, PositiveFloat]]]:
    """Collects k_M values from a COBRA-k model, separating them into substrate and product lists,
       and returns them in ascending order, together with their associated metabolite and reaction IDs.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_M values associated with each metabolite. It distinguishes between substrates
    (metabolites with negative stoichiometry) and products (metabolites with positive
    stoichiometry) and separates the corresponding Kms values into two lists.

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A tuple containing two lists: the first list contains tuples of (reac_id, met_id, k_m) substrates,
        and the second list contains the same for products.
    """
    substrate_kms: list[tuple[str, PositiveFloat]] = []
    product_kms: list[tuple[str, PositiveFloat]] = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if reaction.enzyme_reaction_data is None:
            continue
        for met_id, stoichiometry in reaction.stoichiometries.items():
            if met_id not in reaction.enzyme_reaction_data.k_ms:
                continue
            if return_only_values_with_reference:
                references = reaction.enzyme_reaction_data.k_m_references
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            met_km = reaction.enzyme_reaction_data.k_ms[met_id]
            if stoichiometry < 0:
                substrate_kms.append((reac_id, met_id, met_km))
            else:
                product_kms.append((reac_id, met_id, met_km))
    return sorted(substrate_kms, key=operator.itemgetter(2)), sorted(
        product_kms, key=operator.itemgetter(2)
    )


@validate_call(validate_return=True)
def get_sorted_model_kis(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> list[tuple[str, str, PositiveFloat]]:
    """Collects k_I values from a COBRA-k model and returns them, with reaction and metabolite IDs, in ascending order.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_I values associated with each metabolite

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A list containing the (reac_id, k_I) values
    """
    all_kis: list[tuple[str, PositiveFloat]] = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if reaction.enzyme_reaction_data is None:
            continue
        for met_id, k_i in reaction.enzyme_reaction_data.k_is.items():
            if return_only_values_with_reference:
                references = reaction.enzyme_reaction_data.k_i_references
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            all_kis.append((reac_id, met_id, k_i))
    return sorted(all_kis, key=operator.itemgetter(2))


@validate_call(validate_return=True)
def get_model_kis(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> list[PositiveFloat]:
    """Collects k_I values from a COBRA-k model.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_I values associated with each metabolite

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A list containing the k_I values
    """
    return [
        x[2]
        for x in get_sorted_model_kis(cobrak_model, return_only_values_with_reference)
    ]


@validate_call(validate_return=True)
def get_sorted_model_kas(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> list[tuple[str, str, PositiveFloat]]:
    """Collects k_A values from a COBRA-k model, in ascending order together with associated reaction and metabolite IDs.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_A values associated with each metabolite

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A list containing the (reac_id, met_id, k_A) values
    """
    all_kas: list[tuple[str, PositiveFloat]] = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if reaction.enzyme_reaction_data is None:
            continue
        for met_id, k_a in reaction.enzyme_reaction_data.k_as.items():
            if return_only_values_with_reference:
                references = reaction.enzyme_reaction_data.k_a_references
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            all_kas.append((reac_id, met_id, k_a))
    return sorted(all_kas, key=operator.itemgetter(2))


@validate_call(validate_return=True)
def get_model_kas(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> list[PositiveFloat]:
    """Collects k_A values from a COBRA-k model.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_A values associated with each metabolite

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A list containing the k_A values
    """
    return [
        x[2]
        for x in get_sorted_model_kas(cobrak_model, return_only_values_with_reference)
    ]


@validate_call(validate_return=True)
def get_model_hill_coefficients(
    cobrak_model: Model,
    return_only_values_with_reference: bool = False,
) -> list[PositiveFloat]:
    """Collects k_A values from a COBRA-k model.

    This function iterates through the reactions in a COBRA-k model and extracts the
    k_A values associated with each metabolite

    Args:
        cobrak_model: The COBRA-k Model object.
        return_only_values_with_reference: Returns only values with a given database reference. Defaults to False.

    Returns:
        A tuple containing three lists: the first list contains κ Hill coefficients, the second
        ι Hill coefficients, the third α Hill coefficients.
    """
    kappa_hills: list[PositiveFloat] = []
    iota_hills: list[PositiveFloat] = []
    alpha_hills: list[PositiveFloat] = []
    for reaction in cobrak_model.reactions.values():
        if reaction.enzyme_reaction_data is None:
            continue

        # κ Hills
        for (
            met_id,
            hill_coefficient,
        ) in reaction.enzyme_reaction_data.hill_coefficients.kappa.items():
            if return_only_values_with_reference:
                references = (
                    reaction.enzyme_reaction_data.hill_coefficient_references.kappa
                )
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            kappa_hills.append(hill_coefficient)

        # ι Hills
        for (
            met_id,
            hill_coefficient,
        ) in reaction.enzyme_reaction_data.hill_coefficients.iota.items():
            if return_only_values_with_reference:
                references = (
                    reaction.enzyme_reaction_data.hill_coefficient_references.iota
                )
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            iota_hills.append(hill_coefficient)

        # α Hills
        for (
            met_id,
            hill_coefficient,
        ) in reaction.enzyme_reaction_data.hill_coefficients.alpha.items():
            if return_only_values_with_reference:
                references = (
                    reaction.enzyme_reaction_data.hill_coefficient_references.alpha
                )
                if (met_id not in references) or (len(references[met_id]) == 0):
                    tax_distance = -1
                else:
                    tax_distance = references[met_id][0].tax_distance
                if tax_distance < 0:
                    continue
            alpha_hills.append(hill_coefficient)

    return kappa_hills, iota_hills, alpha_hills


@validate_call(validate_return=True)
def get_model_mws(cobrak_model: Model) -> list[PositiveFloat]:
    """Extracts molecular weights of enzymes from the model.

    Args:
        cobrak_model (Model): The COBRAk model containing enzyme data.

    Returns:
        list[PositiveFloat]: A list of molecular weights for each enzyme in the model.
    """
    mws = []
    for enzyme in cobrak_model.enzymes.values():
        mws.append(enzyme.molecular_weight)
    return mws


@validate_call(validate_return=True)
def get_model_max_kcat_times_e_values(cobrak_model: Model) -> list[NonNegativeFloat]:
    """Calculates the maximum k_cat * E (enzyme concentration in terms of its molecular weight)
    for each reaction with enzyme data and returns these values.

    The maximal k_cat*E is Ω*k_cat/W, with Ω as protein pool and W as enzyme molecular weight.

    Parameters:
        cobrak_model (Model): A metabolic model instance that includes enzymatic constraints,
                              which must contain Reaction instances with enzyme_reaction_data.

    Returns:
        List[float]: A list containing the calculated maximum k_cat * E values for reactions
                     having enzyme reaction data.

    Notes:
        - The function requires 'reaction.enzyme_reaction_data.k_cat' and
          'get_full_enzyme_mw(cobrak_model, reaction)' to be non-zero.
        - If a reaction lacks enzyme reaction data, it is skipped in the calculation.
    """
    max_kcat_times_e_values: list[float] = []
    for reaction in cobrak_model.reactions.values():
        if reaction.enzyme_reaction_data is None:
            continue
        max_kcat_times_e_values.append(
            reaction.enzyme_reaction_data.k_cat
            * cobrak_model.max_prot_pool
            / get_full_enzyme_mw(cobrak_model, reaction)
        )
    return max_kcat_times_e_values


@validate_call(validate_return=True)
def get_model_with_filled_missing_parameters(
    cobrak_model: Model,
    add_dG0_extra_constraints: bool = False,
    param_percentile: conint(ge=0, le=100) = 90,  # pyright: ignore[reportInvalidTypeForm]
    ignore_prefixes: list[str] = ["EX_"],
    use_median_for_kms: bool = True,
    use_median_for_kcats: bool = True,
    ignored_enzyme_ids: list[str] = ["s0001"],
    exclude_bw_reac_ids_for_dG0s: bool = False,
    verbose: bool = False,
) -> Model:
    """Fills missing parameters in a COBRA-k model, including dG0, k_cat, and k_ms values.

    This function iterates through the reactions in a COBRA-k model and fills in missing
    parameters based on percentile values from the entire model.  Missing dG0 values
    are filled using a percentile of the absolute dG0 values.  Missing k_cat values
    are filled using a percentile or median of the k_cat values.  Missing k_ms values
    are filled using a percentile or median of the k_ms values, depending on whether
    the metabolite is a substrate or a product.  Optionally, extra linear constraints
    can be added to enforce consistency between the dG0 values of coupled reversible
    reactions.

    Args:
        cobrak_model: The COBRA-k Model object to be modified.
        add_dG0_extra_constraints: Whether to add extra linear constraints for reversible reactions. Defaults to False.
        param_percentile: The percentile to use for filling missing parameters. Defaults to 90.
        ignore_prefixes: List of prefixes to ignore when processing reactions. Defaults to ["EX_"] (i.e. exchange reactions).
        use_median_for_kms: Whether to use the median instead of the percentile for k_ms values. Defaults to True.
        use_median_for_kcats: Whether to use the median instead of the percentile for k_cat values. Defaults to True.

    Returns:
        A deep copy of the input COBRA-k model with missing parameters filled.
    """
    cobrak_model = deepcopy(cobrak_model)

    all_mws = get_model_mws(cobrak_model)
    all_kcats = get_model_kcats(cobrak_model)
    substrate_kms, product_kms = get_model_kms_by_usage(cobrak_model)
    all_abs_dG0s = [
        abs(dG0)
        for dG0 in get_model_dG0s(
            cobrak_model, exclude_bw_reacs=exclude_bw_reac_ids_for_dG0s
        )
    ]
    if verbose:
        filled_kcats = 0
        filled_dG0s = 0
        filled_substrate_kms = 0
        filled_product_kms = 0
    dG0_reverse_couples: set[tuple[str]] = set()
    for reac_id in cobrak_model.reactions:
        if sum(reac_id.startswith(ignore_prefix) for ignore_prefix in ignore_prefixes):
            continue
        if cobrak_model.reactions[reac_id].dG0 is None:
            reverse_id = get_reverse_reac_id_if_existing(
                reac_id, cobrak_model.fwd_suffix, cobrak_model.rev_suffix
            )
            reverse_id = reverse_id if reverse_id in cobrak_model.reactions else ""
            if add_dG0_extra_constraints and reverse_id:
                dG0_reverse_couples.add(tuple(sorted([reac_id, reverse_id])))
                cobrak_model.reactions[reac_id].dG0 = 0.0
                cobrak_model.reactions[reac_id].dG0_uncertainty = percentile(
                    all_abs_dG0s, param_percentile
                )
            else:
                cobrak_model.reactions[reac_id].dG0 = -percentile(
                    all_abs_dG0s, param_percentile
                )
            if verbose:
                filled_dG0s += 1
        if cobrak_model.reactions[reac_id].enzyme_reaction_data is not None:
            stop = False
            for ignored_enzyme_id in ignored_enzyme_ids:
                for identifier in cobrak_model.reactions[
                    reac_id
                ].enzyme_reaction_data.identifiers:
                    if ignored_enzyme_id in identifier:
                        cobrak_model.reactions[reac_id].enzyme_reaction_data = None
                        stop = True
                        break
                if stop:
                    break
        if (cobrak_model.reactions[reac_id].enzyme_reaction_data is None) or (
            "" in cobrak_model.reactions[reac_id].enzyme_reaction_data.identifiers
        ):
            enzyme_substitue_id = f"{reac_id}_enzyme_substitute"
            if not use_median_for_kcats:
                cobrak_model.reactions[
                    reac_id
                ].enzyme_reaction_data = EnzymeReactionData(
                    identifiers=[enzyme_substitue_id],
                    k_cat=percentile(all_kcats, param_percentile),
                )
            else:
                cobrak_model.reactions[
                    reac_id
                ].enzyme_reaction_data = EnzymeReactionData(
                    identifiers=[enzyme_substitue_id],
                    k_cat=median(all_kcats),
                )
            cobrak_model.enzymes[enzyme_substitue_id] = Enzyme(
                molecular_weight=percentile(all_mws, 100 - param_percentile),
            )
            filled_kcats += 1
        if not have_all_unignored_km(
            cobrak_model.reactions[reac_id], cobrak_model.kinetic_ignored_metabolites
        ):
            existing_kms: list[str] = list(
                cobrak_model.reactions[reac_id].enzyme_reaction_data.k_ms.keys()
            )
            for met_id, stoichiometry in cobrak_model.reactions[
                reac_id
            ].stoichiometries.items():
                if (met_id in cobrak_model.kinetic_ignored_metabolites) or (
                    met_id in existing_kms
                ):
                    continue
                if not use_median_for_kms:
                    cobrak_model.reactions[reac_id].enzyme_reaction_data.k_ms[
                        met_id
                    ] = float(
                        percentile(
                            product_kms if stoichiometry > 0.0 else substrate_kms,
                            param_percentile
                            if stoichiometry > 0.0
                            else 100 - param_percentile,
                        )
                    )
                else:
                    cobrak_model.reactions[reac_id].enzyme_reaction_data.k_ms[
                        met_id
                    ] = (
                        median(substrate_kms)
                        if stoichiometry < 0.0
                        else median(product_kms)
                    )
                if verbose:
                    if stoichiometry > 0.0:
                        filled_product_kms += 1
                    else:
                        filled_substrate_kms += 1

    for dG0_reverse_couple in dG0_reverse_couples:
        reac_id_1, reac_id_2 = dG0_reverse_couple
        cobrak_model.extra_linear_constraints.append(
            ExtraLinearConstraint(
                stoichiometries={
                    f"{DG0_VAR_PREFIX}{reac_id_1}": 1.0,
                    f"{DG0_VAR_PREFIX}{reac_id_2}": 1.0,
                },
                lower_value=0.0,
                upper_value=0.0,
            )
        )

    if verbose:
        print("# filled kcats:", filled_kcats)
        print("# filled substrate kms:", filled_substrate_kms)
        print("# filled product kms:", filled_product_kms)
        print("# filled kms in total:", filled_product_kms + filled_substrate_kms)
        print("# filled ΔG'° values:", filled_dG0s)

    return cobrak_model


@validate_call(validate_return=True)
def get_reaction_string(cobrak_model: Model, reac_id: str) -> str:
    """Generate a string representation of a reaction in a COBRAk model.

    This function constructs a string that represents the stoichiometry of a specified reaction,
    including the direction of the reaction based on its flux bounds. E.g., a reaction
    R1: A ⇒ B, [0, 1000]
    is returned
    as "1 A ⇒ 1 B"

    Args:
        cobrak_model (Model): The COBRAk model containing the reaction.
        reac_id (str): The ID of the reaction to be represented as a string.

    Returns:
        str: A string representation of the reaction, showing educts, products, and the reaction direction.
    """
    reaction = cobrak_model.reactions[reac_id]
    educt_parts = []
    product_parts = []
    for met_id, stoichiometry in reaction.stoichiometries.items():
        met_string = f"{stoichiometry} {met_id}"
        if stoichiometry > 0:
            product_parts.append(met_string)
        else:
            educt_parts.append(met_string)
    if (reaction.min_flux < 0) and (reaction.max_flux > 0):
        arrow = "⇔"
    elif (reaction.min_flux < 0) and (reaction.max_flux <= 0):
        arrow = "⇐"
    else:
        arrow = "⇒"

    return " + ".join(educt_parts) + " " + arrow + " " + " + ".join(product_parts)


@validate_call(validate_return=True)
def get_reverse_reac_id_if_existing(
    reac_id: str,
    fwd_suffix: str = REAC_FWD_SUFFIX,
    rev_suffix: str = REAC_REV_SUFFIX,
) -> str:
    """Returns the ID of the reverse reaction if it exists, otherwise returns an empty string.

    Args:
    reac_id (str): The ID of the reaction.
    fwd_suffix (str, optional): The suffix used to identify forward reactions. Defaults to REAC_FWD_SUFFIX.
    rev_suffix (str, optional): The suffix used to identify reverse reactions. Defaults to REAC_REV_SUFFIX.

    Returns:
    str: The ID of the reverse reaction if it exists, otherwise an empty string.
    """
    if reac_id.endswith(fwd_suffix):
        return reac_id.replace(fwd_suffix, rev_suffix)
    if reac_id.endswith(rev_suffix):
        return reac_id.replace(rev_suffix, fwd_suffix)
    return ""


@validate_call(validate_return=True)
def get_metabolites_in_elementary_conservation_relations(
    cobrak_model: Model,
) -> list[str]:
    """Identify metabolites involved in elementary conservation relations (ECRs) in a COBRAk model.

    Calculates the null space of the stoichiometric matrix of a COBRAk model to determine the elementary conservation relations.
    It then identifies the metabolites that are part of these relations.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and metabolites.

    Returns:
        list[str]: A list of metabolite IDs that are involved in elementary conservation relations.
    """
    # Convert the list of lists to a sympy Matrix
    S_matrix = array(get_stoichiometric_matrix(cobrak_model)).T

    # Calculate the null space of the stoichiometric matrix using Gaussian elimination
    null_spacex = null_space(S_matrix)

    # Convert the null space vectors to a NumPy array
    ECRs = (
        null_spacex.T
    )  # np.array([ns.T.tolist()[0] for ns in null_spacex], dtype=float)

    # Simplify the ECRs by removing near-zero elements
    threshold = 1e-10
    ECRs[np.abs(ECRs) < threshold] = 0
    met_ids = list(cobrak_model.metabolites)

    dependencies = []
    for ecr in ECRs.tolist():
        for entry_num in range(len(ecr)):
            if ecr[entry_num] != 0.0:
                dependencies.append(met_ids[entry_num])
    return list(set(dependencies))


@validate_call(validate_return=True)
def get_model_with_varied_parameters(
    model: Model,
    max_km_variation: NonNegativeFloat | None = None,
    max_kcat_variation: NonNegativeFloat | None = None,
    max_ki_variation: NonNegativeFloat | None = None,
    max_ka_variation: NonNegativeFloat | None = None,
    max_dG0_variation: NonNegativeFloat | None = None,
    varied_reacs: list[str] = [],
    change_unknown_values: bool = True,
    change_known_values: bool = True,
    use_shuffling_instead_of_uniform_random: bool = False,
    use_shuffling_with_putting_back: bool = False,
    shuffle_using_distribution_of_values_with_reference: bool = True,
) -> Model:
    """Generates a modified copy of the input Model with varied reaction parameters.

    This function creates a deep copy of the input Model and introduces random variations
    to several reaction parameters, including dG0, k_cat, k_ms, k_is, and k_as.  The
    magnitude of the variation is controlled by the provided `max_..._variation`
    parameters.  If a `max_..._variation` parameter is not provided (i.e., is None),
    the corresponding parameter will not be varied.  Variations are applied randomly
    using a uniform distribution.  For reactions with a reverse reaction, the dG0 values
    of the forward and reverse reactions are updated to maintain thermodynamic consistency.

    Args:
        model: The Model object to be modified.
        max_km_variation: Maximum factor by which to vary Kms.  Defaults to None.
            No effect (except if it is None, then nothing happens) if ```use_shuffling_instead_of_uniform_random=True```.
        max_kcat_variation: Maximum factor by which to vary k_cat. Defaults to None.
            No effect (except if it is None, then nothing happens) if ```use_shuffling_instead_of_uniform_random=True```.
        max_ki_variation: Maximum factor by which to vary k_is. Defaults to None.
            No effect (except if it is None, then nothing happens) if ```use_shuffling_instead_of_uniform_random=True```.
        max_ka_variation: Maximum factor by which to vary k_as. Defaults to None.
            No effect (except if it is None, then nothing happens) if ```use_shuffling_instead_of_uniform_random=True```.
        max_dG0_variation: Maximum factor by which to vary dG0. Defaults to None.
            No effect (except if it is None, then nothing happens) if ```use_shuffling_instead_of_uniform_random=True```.
        varied_reacs: If not [], only reactions with IDs in this list are varied. Defaults to [].
        change_known_values: Change values if they *are* set with a
            taxonomic distance in their reference. Defaults to True.
        change_unknown_values: Change values if they are *not* set with a
            taxonomic distance in their reference. Defaults to True.
        use_shuffling_instead_of_uniform_random: Overwrites max variation parameters, and switches
            to shuffling inside the known kcats, educt kms, product kms and so on.
        shuffle_using_distribution_of_values_with_reference: If True (the default), the shuffling will only
            choose values with a reference for the shuffling; note that if ```change_unknown_values=True```,
            the unknown values will still be shuffled, but if ```shuffle_using_distribution_of_values_with_reference=True````
            just using the distribution with values with references.

    Returns:
        A deep copy of the input model with varied reaction parameters.
    """
    varied_model = deepcopy(model)
    tested_rev_reacs: list[str] = []
    if use_shuffling_instead_of_uniform_random:
        if max_km_variation is not None:
            substrate_kms, product_kms = get_model_kms_by_usage(
                model,
                return_only_values_with_reference=shuffle_using_distribution_of_values_with_reference,
            )
            all_substrate_km_indices = list(range(len(substrate_kms)))
            all_product_km_indices = list(range(len(product_kms)))
        if max_dG0_variation is not None:
            all_dG0s = get_model_dG0s(model)
            all_dG0_indices = list(range(len(all_dG0s)))
        if max_kcat_variation is not None:
            all_kcats = get_model_kcats(model)
            all_kcat_indices = list(range(len(all_kcats)))
        if max_ki_variation is not None:
            all_kis = get_model_kis(model)
            all_ki_indices = list(range(len(all_kis)))
        if max_ka_variation is not None:
            all_kas = get_model_kas(model)
            all_ka_indices = list(range(len(all_kas)))
    for reac_id, reaction in varied_model.reactions.items():
        if (varied_reacs != []) and (reac_id not in varied_reacs):
            continue
        if (
            max_dG0_variation is not None
            and reaction.dG0 is not None
            and reac_id not in tested_rev_reacs
        ):
            if use_shuffling_instead_of_uniform_random:
                if not use_shuffling_with_putting_back:
                    chosen_index = choice(all_dG0_indices)
                    reaction.dG0 = all_dG0s[chosen_index]
                    del all_dG0_indices[all_dG0_indices.index(chosen_index)]
                else:
                    reaction.dG0 = choice(all_dG0s)
            else:
                reaction.dG0 += uniform(-max_dG0_variation, +max_dG0_variation)  # noqa: NPY002
            rev_id = get_reverse_reac_id_if_existing(
                reac_id=reac_id,
                fwd_suffix=varied_model.fwd_suffix,
                rev_suffix=varied_model.rev_suffix,
            )
            if rev_id in varied_model.reactions:
                varied_model.reactions[rev_id].dG0 = -reaction.dG0
                tested_rev_reacs.append(rev_id)
        if reaction.enzyme_reaction_data is not None:
            if max_kcat_variation is not None:
                kcat_tax_distance = (
                    -1
                    if len(reaction.enzyme_reaction_data.k_cat_references) == 0
                    else reaction.enzyme_reaction_data.k_cat_references[0].tax_distance
                )
                if (change_known_values and kcat_tax_distance >= 0) or (
                    change_unknown_values and kcat_tax_distance < 0
                ):
                    if use_shuffling_instead_of_uniform_random:
                        if not use_shuffling_with_putting_back:
                            chosen_index = choice(all_kcat_indices)
                            reaction.enzyme_reaction_data.k_cat = all_kcats[
                                chosen_index
                            ]
                            del all_kcat_indices[all_kcat_indices.index(chosen_index)]
                        else:
                            reaction.enzyme_reaction_data.k_cat = choice(all_kcats)
                    else:
                        reaction.enzyme_reaction_data.k_cat *= max_kcat_variation ** (
                            uniform(-1, 1)  # noqa: NPY002
                        )  # noqa: NPY002
            if max_km_variation is not None:
                for met_id in reaction.enzyme_reaction_data.k_ms:
                    references = reaction.enzyme_reaction_data.k_m_references
                    km_tax_distance = (
                        -1
                        if met_id not in references or len(references[met_id]) == 0
                        else references[met_id][0].tax_distance
                    )
                    if not (
                        (change_known_values and km_tax_distance >= 0)
                        or (change_unknown_values and km_tax_distance < 0)
                    ):
                        continue
                    if (
                        met_id in reaction.stoichiometries
                        and reaction.stoichiometries[met_id] < 0.0
                    ):  # Substrate k_ms
                        if use_shuffling_instead_of_uniform_random:
                            chosen_index = choice(all_substrate_km_indices)
                            if not use_shuffling_with_putting_back:
                                reaction.enzyme_reaction_data.k_ms[met_id] = (
                                    substrate_kms[chosen_index]
                                )
                                del all_substrate_km_indices[
                                    all_substrate_km_indices.index(chosen_index)
                                ]
                            else:
                                reaction.enzyme_reaction_data.k_ms[met_id] = choice(
                                    substrate_kms
                                )
                        else:
                            reaction.enzyme_reaction_data.k_ms[met_id] *= (
                                max_km_variation ** (uniform(-1, 1))  # noqa: NPY002
                            )  # noqa: NPY002
                    else:  # Product k_ms
                        if use_shuffling_instead_of_uniform_random:
                            if not use_shuffling_with_putting_back:
                                chosen_index = choice(all_product_km_indices)
                                reaction.enzyme_reaction_data.k_ms[met_id] = (
                                    product_kms[chosen_index]
                                )
                                del all_product_km_indices[
                                    all_product_km_indices.index(chosen_index)
                                ]
                            else:
                                reaction.enzyme_reaction_data.k_ms[met_id] = choice(
                                    product_kms
                                )
                        else:
                            reaction.enzyme_reaction_data.k_ms[met_id] *= (
                                max_km_variation ** (uniform(-1, 1))  # noqa: NPY002
                            )  # noqa: NPY002
            if max_ki_variation is not None:
                references = reaction.enzyme_reaction_data.k_i_references
                ki_tax_distance = (
                    -1
                    if met_id not in references or len(references[met_id]) == 0
                    else references[met_id][0].tax_distance
                )
                if not (
                    (change_known_values and ki_tax_distance >= 0)
                    or (change_unknown_values and ki_tax_distance < 0)
                ):
                    continue
                for met_id in reaction.enzyme_reaction_data.k_is:
                    if use_shuffling_instead_of_uniform_random:
                        if not use_shuffling_with_putting_back:
                            chosen_index = choice(all_substrate_km_indices)
                            reaction.enzyme_reaction_data.k_is[met_id] = all_kis[
                                chosen_index
                            ]
                            del all_ki_indices[all_ki_indices.index(chosen_index)]
                        else:
                            reaction.enzyme_reaction_data.k_is[met_id] = choice(all_kis)
                    else:
                        reaction.enzyme_reaction_data.k_is[met_id] *= (
                            max_ki_variation
                            ** (
                                uniform(-1, 1)  # noqa: NPY002
                            )
                        )  # noqa: NPY002
            if max_ka_variation is not None:
                references = reaction.enzyme_reaction_data.k_a_references
                ka_tax_distance = (
                    -1
                    if met_id not in references or len(references[met_id]) == 0
                    else references[met_id][0].tax_distance
                )
                if not (
                    (change_known_values and ka_tax_distance >= 0)
                    or (change_unknown_values and ka_tax_distance < 0)
                ):
                    continue
                for met_id in reaction.enzyme_reaction_data.k_as:
                    if use_shuffling_instead_of_uniform_random:
                        if not use_shuffling_with_putting_back:
                            chosen_index = choice(all_ka_indices)
                            reaction.enzyme_reaction_data.k_as[met_id] = all_kas[
                                chosen_index
                            ]
                            del all_ka_indices[all_ka_indices.index(chosen_index)]
                        else:
                            reaction.enzyme_reaction_data.k_as[met_id] = choice(all_kas)
                    else:
                        reaction.enzyme_reaction_data.k_as[met_id] *= (
                            max_ka_variation
                            ** (
                                uniform(-1, 1)  # noqa: NPY002
                            )
                        )  # noqa: NPY002
    return varied_model


@validate_call(validate_return=True)
def get_potentially_active_reactions_in_variability_dict(
    cobrak_model: Model, variability_dict: dict[str, tuple[float, float]]
) -> list[str]:
    """Identify potentially active reactions in a COBRAk model based on a variability dictionary.

    This function returns a list of reaction IDs that are present in both the COBRAk model and the variability dictionary,
    and have a maximum flux greater than zero while having a minimum flux equal to zero. These reactions are considered potentially active.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions.
        variability_dict (dict[str, tuple[float, float]]): A dictionary mapping reaction IDs to their minimum and maximum flux values.

    Returns:
        list[str]: A list of reaction IDs that are potentially active.
    """
    return [
        reac_id
        for reac_id in variability_dict
        if (reac_id in cobrak_model.reactions)
        and (variability_dict[reac_id][1] > 0.0)
        and (variability_dict[reac_id][0] <= 0.0)
    ]


def get_pyomo_solution_as_dict(model: ConcreteModel) -> dict[str, float]:
    """Returns the pyomo solution as a dictionary of { "$VAR_NAME": "$VAR_VALUE", ... }

    Value is None for all uninitialized variables.

    Args:
        model (ConcreteModel): The pyomo model

    Returns:
        dict[str, float]: The solution dictionary
    """
    model_var_names = [v.name for v in model.component_objects(Var)]
    solution_dict = {}
    for model_var_name in model_var_names:
        try:
            var_value = getattr(model, model_var_name).value
        except ValueError:
            var_value = None  # Uninitialized variable (e.g., x_Biomass)
        solution_dict[model_var_name] = var_value
    return solution_dict


@validate_call(validate_return=True)
def get_reaction_enzyme_var_id(reac_id: str, reaction: Reaction) -> str:
    """Returns the pyomo model name of the reaction's enzyme

    Args:
        reac_id (str): Reaction ID
        reaction (Reaction): Reaction instance

    Returns:
        str: Reaction enzyme's name
    """
    if reaction.enzyme_reaction_data is None:
        return ""
    return (
        ENZYME_VAR_PREFIX
        + get_full_enzyme_id(reaction.enzyme_reaction_data.identifiers)
        + ENZYME_VAR_INFIX
        + reac_id
    )


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def get_solver_status_from_pyomo_results(
    pyomo_results: SolverResults,
) -> NonNegativeInt:
    """Returns the solver status from the pyomo results as an integer code.

    This function interprets the solver status from a `SolverResults` object and returns a corresponding integer code.
    The mapping is as follows:
    - 0 for `SolverStatus.ok`
    - 1 for `SolverStatus.warning`
    - 2 for `SolverStatus.error`
    - 3 for `SolverStatus.aborted`
    - 4 for `SolverStatus.unknown`

    Args:
        pyomo_results (SolverResults): The results object from a Pyomo solver containing the solver status.

    Raises:
        ValueError: If the solver status is not recognized.

    Returns:
        int: An integer code representing the solver status.
    """
    match pyomo_results.solver.status:
        case SolverStatus.ok:
            return 0
        case SolverStatus.warning:
            return 1
        case SolverStatus.error:
            return 2
        case SolverStatus.aborted:
            return 3
        case SolverStatus.unknown:
            return 4
        case _:
            raise ValueError


@validate_call(validate_return=True)
def get_stoichiometric_matrix(cobrak_model: Model) -> list[list[float]]:
    """Returns the model's stoichiometric matrix.

    The matrix is returned as a list of float lists, where each float list
    stands for a reaction and each entry in the float list for a metabolite.

    Args:
        cobrak_model (Model): The model

    Returns:
        list[list[float]]: The stoichiometric matrix
    """
    matrix: list[list[float]] = []
    for met_id in cobrak_model.metabolites:
        met_row: list[float] = []
        for reac_data in cobrak_model.reactions.values():
            if met_id in reac_data.stoichiometries:
                met_row.append(reac_data.stoichiometries[met_id])
            else:
                met_row.append(0.0)
        matrix.append(met_row.copy())
    return matrix


@validate_call(validate_return=True)
def get_stoichiometrically_coupled_reactions(
    cobrak_model: Model, rounding: NonNegativeInt = 10
) -> list[list[str]]:
    """Returns stoichiometrically coupled reactions.

    The returned format is as follows: Say that reactions (R1 & R2) as well
    as (R5 & R6 & R7) are stoichiometrically coupled (i.e, their fluxes are
    in a strict linear relationship to each other), then this function
    returns [["R1", "R2"], ["R5", "R6", "R7"].

    The identification of stoichiometrically coupled reactions happens through
    the calculation of the model's stoichiometric matrix nullspace.

    Args:
        cobrak_model (Model): The model
        rounding (int, optional): Precision for the calculation of the nullspace. Defaults to 10.

    Returns:
        list[list[str]]: The stoichiometrically coupled reactions
    """
    # Calculate nullspace and convert each row to rounded tuples
    null_space_matrix = null_space(get_stoichiometric_matrix(cobrak_model))
    null_space_tuples = [
        tuple(round(value, rounding) for value in row) for row in null_space_matrix
    ]

    # Map the null space tuples to reaction indices
    occcurences: dict[tuple[float, ...], list[int]] = {}
    for reac_idx, null_space_tuple in enumerate(null_space_tuples):
        if null_space_tuple not in occcurences:
            occcurences[null_space_tuple] = []
        occcurences[null_space_tuple].append(reac_idx)

    # Map the reaction indices to the final couples reactions list
    coupled_reacs: list[list[str]] = []
    reac_ids = list(cobrak_model.reactions.keys())
    for coupled_indices in occcurences.values():
        coupled_reacs.append([reac_ids[reac_idx] for reac_idx in coupled_indices])

    return coupled_reacs


@validate_call(validate_return=True)
def get_substrate_and_product_exchanges(
    cobrak_model: Model, optimization_dict: dict[str, Any] = {}
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Identifies and categorizes reactions as substrate or product exchanges based on reaction stoichiometries.

    This function analyzes each reaction in the provided COBRAk model to determine whether it primarily represents substrate consumption or product formation.
    It categorizes reactions into substrate reactions (where all stoichiometries are positive, indicating metabolite consumption) and product reactions
    (where all stoichiometries are negative, indicating metabolite production).

    * A reaction is classified as a substrate reaction if all its stoichiometries are positive, indicating that all metabolites involved are being consumed.
    * A reaction is classified as a product reaction if all its stoichiometries are negative, indicating that all metabolites involved are being produced.
    * If the `optimization_dict` is provided, only the reactions listed in this dictionary are considered for classification.
    * The function returns tuples of reaction IDs, which can be used for further processing or analysis of substrate and product reactions.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions to be analyzed.
        optimization_dict (dict[str, Any], optional): An optional dictionary to filter reactions. Only reactions whose IDs are present in this dictionary will be considered.
        Defaults to {}.

    Returns:
        tuple[tuple[str, ...], tuple[str, ...]]: A tuple containing two elements:
            - The first element is a tuple of reaction IDs identified as substrate reactions.
            - The second element is a tuple of reaction IDs identified as product reactions.
    """
    substrate_reac_ids: list[str] = []
    product_reac_ids: list[str] = []
    for reac_id, reaction in cobrak_model.reactions.items():
        if optimization_dict != {} and reac_id not in optimization_dict:
            continue
        stoichiometries = list(reaction.stoichiometries.values())
        if min(stoichiometries) > 0 and max(stoichiometries) > 0:
            substrate_reac_ids.append(reac_id)
        elif min(stoichiometries) < 0 and max(stoichiometries) < 0:
            product_reac_ids.append(reac_id)
    return tuple(substrate_reac_ids), tuple(product_reac_ids)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def get_termination_condition_from_pyomo_results(
    pyomo_results: SolverResults,
) -> NonNegativeFloat:
    """Returns the termination condition from the pyomo results as a float code.

    This function interprets the termination condition from a `SolverResults` object and returns a corresponding float code.
    The mapping is as follows:
    - 0.1 for `TerminationCondition.globallyOptimal`
    - 0.2 for `TerminationCondition.optimal`
    - 0.3 for `TerminationCondition.locallyOptimal`
    - 1 for `TerminationCondition.maxTimeLimit`
    - 2 for `TerminationCondition.maxIterations`
    - 3 for `TerminationCondition.minFunctionValue`
    - 4 for `TerminationCondition.minStepLength`
    - 5 for `TerminationCondition.maxEvaluations`
    - 6 for `TerminationCondition.other`
    - 7 for `TerminationCondition.unbounded`
    - 8 for `TerminationCondition.infeasible`
    - 9 for `TerminationCondition.invalidProblem`
    - 10 for `TerminationCondition.solverFailure`
    - 11 for `TerminationCondition.internalSolverError`
    - 12 for `TerminationCondition.error`
    - 13 for `TerminationCondition.userInterrupt`
    - 14 for `TerminationCondition.resourceInterrupt`
    - 15 for `TerminationCondition.licensingProblem`

    Args:
        pyomo_results (SolverResults): The results object from a Pyomo solver containing the termination condition.

    Raises:
        ValueError: If the termination condition is not recognized.

    Returns:
        float: A float code representing the termination condition.
    """
    match pyomo_results.solver.termination_condition:
        case TerminationCondition.globallyOptimal:
            return 0.1
        case TerminationCondition.optimal:
            return 0.2
        case TerminationCondition.locallyOptimal:
            return 0.3
        case TerminationCondition.maxTimeLimit:
            return 1
        case TerminationCondition.maxIterations:
            return 2
        case TerminationCondition.minFunctionValue:
            return 3
        case TerminationCondition.minStepLength:
            return 4
        case TerminationCondition.maxEvaluations:
            return 5
        case TerminationCondition.other:
            return 6
        case TerminationCondition.unbounded:
            return 7
        case TerminationCondition.infeasible:
            return 8
        case TerminationCondition.invalidProblem:
            return 9
        case TerminationCondition.solverFailure:
            return 10
        case TerminationCondition.internalSolverError:
            return 11
        case TerminationCondition.error:
            return 12
        case TerminationCondition.userInterrupt:
            return 13
        case TerminationCondition.resourceInterrupt:
            return 14
        case TerminationCondition.licensingProblems:
            return 15
        case TerminationCondition.intermediateNonInteger:
            return 16
        case _:
            raise ValueError


@validate_call(validate_return=True)
def get_unoptimized_reactions_in_nlp_solution(
    cobrak_model: Model,
    solution: dict[str, float],
    verbose: bool = False,
    regard_iota: bool = False,
    regard_alpha: bool = False,
) -> dict[str, tuple[float, float]]:
    """Identify unoptimized reactions in the NLP (Non-Linear Programming) solution.

    This function checks each reaction in the COBRAk model to determine if the flux values in the provided NLP solution match
    the expected values based on enzyme kinetics and thermodynamics.
    Reactions with discrepancies are considered unoptimized and are returned in a dictionary.

    Discrepancies occur because, in COBRAk, the saturation term and the thermodynamic restriction are set as maximal values (<=),
    they are not fixed.

    Args:
        cobrak_model (Model): The COBRAk model containing reactions and enzyme data.
        solution (dict[str, float]): A dictionary mapping variable names to their values from an NLP solution.
        verbose: bool: Whether or not to print the discrepancies for each reaction

    Returns:
        dict[str, tuple[float, float]]: Dictionary where the keys are reaction IDs and the values are
                                        tuples containing the NLP solution flux and the real flux for unoptimized reactions.
    """
    unoptimized_reactions: dict[str, tuple[float, float]] = {}
    RT = cobrak_model.R * cobrak_model.T

    for reac_id, reaction in cobrak_model.reactions.items():
        if reac_id not in solution:
            continue
        if reaction.enzyme_reaction_data is None:
            continue
        if reaction.enzyme_reaction_data.identifiers == [""]:
            continue

        nlp_flux = solution[reac_id]
        has_problem = False

        # Kappa check
        if have_all_unignored_km(reaction, cobrak_model.kinetic_ignored_metabolites):
            kappa_substrates = 1.0
            kappa_products = 1.0
            for met_id, raw_stoichiometry in reaction.stoichiometries.items():
                if met_id in cobrak_model.kinetic_ignored_metabolites:
                    continue

                stoichiometry = (
                    raw_stoichiometry
                    * reaction.enzyme_reaction_data.hill_coefficients.kappa.get(
                        met_id, 1.0
                    )
                )
                expconc = exp(solution[f"{LNCONC_VAR_PREFIX}{met_id}"])
                multiplier = (
                    expconc / reaction.enzyme_reaction_data.k_ms[met_id]
                ) ** abs(stoichiometry)
                if stoichiometry < 0.0:
                    kappa_substrates *= multiplier
                else:
                    kappa_products *= multiplier

            real_kappa = kappa_substrates / (1 + kappa_substrates + kappa_products)
            nlp_kappa = solution[f"{KAPPA_VAR_PREFIX}{reac_id}"]

            if abs(nlp_kappa - real_kappa) > 0.001:
                has_problem = True
                if verbose:
                    print(
                        f"κ problem in {reac_id}: Real is {real_kappa}, NLP value is {nlp_kappa}"
                    )
        else:
            real_kappa = 1.0
            nlp_kappa = 1.0

        # Iota and alpha check
        real_iota = 1.0
        real_alpha = 1.0
        if (
            reac_id in solution
            and reaction.enzyme_reaction_data is not None
            and reaction.enzyme_reaction_data.identifiers != [""]
        ):
            alpha_and_iota_mets = set(
                list(reaction.enzyme_reaction_data.k_is.keys())
                + list(reaction.enzyme_reaction_data.k_as.keys())
            )
            for met_id in alpha_and_iota_mets:
                met_var_id = f"{LNCONC_VAR_PREFIX}{met_id}"
                if met_var_id not in solution:
                    continue
                expconc = exp(solution[met_var_id])
                stoichiometry_iota = abs(
                    reaction.stoichiometries.get(met_id, 1.0)
                ) * reaction.enzyme_reaction_data.hill_coefficients.iota.get(
                    met_id, 1.0
                )
                stoichiometry_alpha = abs(
                    reaction.stoichiometries.get(met_id, 1.0)
                ) * reaction.enzyme_reaction_data.hill_coefficients.alpha.get(
                    met_id, 1.0
                )

                if met_id in reaction.enzyme_reaction_data.k_is and regard_iota:
                    real_iota *= 1 / (
                        1
                        + (expconc / reaction.enzyme_reaction_data.k_is[met_id])
                        ** stoichiometry_iota
                    )
                if met_id in reaction.enzyme_reaction_data.k_as and regard_alpha:
                    real_alpha *= 1 / (
                        1
                        + (reaction.enzyme_reaction_data.k_as[met_id] / expconc)
                        ** stoichiometry_alpha
                    )

        nlp_iota = (
            solution.get(f"{IOTA_VAR_PREFIX}{reac_id}", 1.0) if regard_iota else 1.0
        )
        if abs(nlp_iota - real_iota) > 0.001:
            has_problem = True
            if verbose:
                print(
                    f"ι problem in {reac_id}: Real is {real_iota}, NLP value is {nlp_iota}"
                )
        nlp_alpha = (
            solution.get(f"{ALPHA_VAR_PREFIX}{reac_id}", 1.0) if regard_alpha else 1.0
        )
        if abs(nlp_alpha - real_alpha) > 0.001:
            has_problem = True
            if verbose:
                print(
                    f"α problem in {reac_id}: Real is {real_alpha}, NLP value is {nlp_alpha}"
                )

        # Gamma check
        if reaction.dG0 is not None:
            gamma_substrates = 1.0
            gamma_products = 1.0

            for met_id, stoichiometry in reaction.stoichiometries.items():
                multiplier = exp(solution[f"{LNCONC_VAR_PREFIX}{met_id}"]) ** abs(
                    stoichiometry
                )
                if stoichiometry < 0.0:
                    gamma_substrates *= multiplier
                else:
                    gamma_products *= multiplier

            dg = -(reaction.dG0 + RT * log(gamma_products) - RT * log(gamma_substrates))
            real_gamma = 1 - exp(-dg / RT)
            nlp_gamma = solution[f"{GAMMA_VAR_PREFIX}{reac_id}"]

            if abs(nlp_gamma - real_gamma) > 0.001:
                has_problem = True
                if verbose:
                    print(
                        f"γ problem in {reac_id}: Real is {real_gamma}, NLP value is {nlp_gamma}"
                    )
                    print(
                        f"ΔG': Real is {dg}, NLP value is {solution[DF_VAR_PREFIX + reac_id]}"
                    )
                    print("E", solution[get_reaction_enzyme_var_id(reac_id, reaction)])
                    print(
                        "E_use",
                        solution[get_reaction_enzyme_var_id(reac_id, reaction)]
                        * get_full_enzyme_mw(cobrak_model, reaction),
                    )
        else:
            real_gamma = 1.0
            nlp_gamma = 1.0

        # V plus
        enzyme_conc = solution[get_reaction_enzyme_var_id(reac_id, reaction)]
        v_plus = enzyme_conc * reaction.enzyme_reaction_data.k_cat

        nlp_flux = v_plus * nlp_gamma * nlp_kappa * nlp_alpha * nlp_iota
        real_flux = v_plus * real_gamma * real_kappa * real_alpha * real_iota
        if has_problem and verbose:
            print(nlp_flux, real_flux, solution[reac_id])

        if real_flux != solution[reac_id]:
            unoptimized_reactions[reac_id] = (solution[reac_id], real_flux)

    return unoptimized_reactions


@validate_call(validate_return=True)
def have_all_unignored_km(
    reaction: Reaction, kinetic_ignored_metabolites: list[str]
) -> bool:
    """Check if all non-ignored metabolites in a reaction have associated Michaelis-Menten constants (k_m).

    This function checks whether all substrates and products of a reaction, excluding those specified in the kinetically ignored metabolites list,
    have associated Km values. It also ensures that there is at least one substrate and one product with a k_m value.

    Args:
        reaction (Reaction): The reaction to be checked.
        kinetic_ignored_metabolites (list[str]): A list of metabolite IDs to be ignored in the k_m check.

    Returns:
        bool: True if all non-ignored metabolites have Km values and there is at least one substrate and one product with Km values, False otherwise.
    """
    if reaction.enzyme_reaction_data is None:
        return False

    eligible_mets = [
        met_id
        for met_id, stoichiometry in reaction.stoichiometries.items()
        if met_id not in kinetic_ignored_metabolites
    ]
    for eligible_met in eligible_mets:
        if eligible_met not in reaction.enzyme_reaction_data.k_ms:
            return False

    substrates_with_km = [
        met_id
        for met_id in eligible_mets
        if (met_id in reaction.enzyme_reaction_data.k_ms)
        and (reaction.stoichiometries[met_id] < 0)
    ]
    products_with_km = [
        met_id
        for met_id in eligible_mets
        if (met_id in reaction.enzyme_reaction_data.k_ms)
        and (reaction.stoichiometries[met_id] > 0)
    ]
    return not (len(substrates_with_km) == 0 or len(products_with_km) == 0)


@validate_call(validate_return=True)
def is_any_error_term_active(correction_config: CorrectionConfig) -> bool:
    """Checks if any error term is active in the correction configuration.

    This function determines whether any of the error terms specified in the
    `CorrectionConfig` object are enabled.  It sums the boolean values of the
    flags indicating whether each error term is active.  If the sum is greater
    than zero, it means at least one error term is active.

    Args:
        correction_config: The CorrectionConfig object to check.

    Returns:
        True if at least one error term is active, False otherwise.
    """
    return bool(
        sum(
            [
                correction_config.add_flux_error_term,
                correction_config.add_met_logconc_error_term,
                correction_config.add_enzyme_conc_error_term,
                correction_config.add_kcat_times_e_error_term,
                correction_config.add_dG0_error_term,
                correction_config.add_km_error_term,
            ]
        )
    )


@validate_call(validate_return=True)
def is_objsense_maximization(objsense: int) -> bool:
    """Checks if the objective sense is maximization.

    Args:
    objsense (int): The objective sense, where in this function's definition:
    - >0: Maximization
    - ≤0: Minimization

    Returns:
    bool: True if the objective sense is maximization, False otherwise."""
    return objsense > 0


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def last_n_elements_equal(lst: list[Any], n: int | float) -> bool:
    """Check if the last n elements of a list are equal.

    Args:
        lst (list[Any]): The list to check.
        n (int): The number of elements from the end of the list to compare.

    Returns:
        bool: True if the last n elements are equal, False otherwise.

    Example:
        >>> last_n_elements_equal([1, 2, 3, 4, 4, 4], 3)
        True
        >>> last_n_elements_equal([1, 2, 3, 4, 5, 6], 3)
        False
    """
    return (n == 0) or (len(lst) >= n and all(x == lst[-n] for x in lst[-n:]))


@validate_call(validate_return=True)
def make_kms_better_by_factor(
    cobrak_model: Model, reac_id: str, factor: NonNegativeFloat
) -> None:
    """Adjusts the Michaelis constants (Km) for substrates and products of a specified reaction in the metabolic model.

    - Substrate's Michaelis constants are divided by 'factor'.
    - Product's Michaelis constants are multiplied by 'factor'.
    - Only affects metabolites with existing enzyme reaction data.

    Parameters:
        cobrak_model (Model): The metabolic model containing enzymatic constraints.
        reac_id (str): The ID of the reaction to adjust the Km values for.
        factor (float): The multiplication/division factor used to modify the Michaelis constants.

    Returns:
        None: This function modifies the input Model object in place and does not return any value.
    """
    reaction = cobrak_model.reactions[reac_id]

    substrate_ids = [
        met_id
        for met_id in reaction.stoichiometries
        if reaction.stoichiometries[met_id] < 0
    ]
    for substrate_id in substrate_ids:
        if substrate_id not in reaction.enzyme_reaction_data.k_ms:
            continue
        reaction.enzyme_reaction_data.k_ms[substrate_id] /= factor

    product_ids = [
        met_id
        for met_id in reaction.stoichiometries
        if reaction.stoichiometries[met_id] > 0
    ]
    for product_id in product_ids:
        if product_id not in reaction.enzyme_reaction_data.k_ms:
            continue
        reaction.enzyme_reaction_data.k_ms[product_id] *= factor


@validate_call(validate_return=True)
def parse_external_resources(
    path: str, brenda_version: str, parse_brenda: bool = True
) -> None:
    """Parse and verify the presence of external resource files required for a COBRAk model.

    This function checks if the necessary external resource files are present in the specified directory.
    If any required files are missing, it provides instructions on where to download them. Additionally,
    it processes certain files if their parsed versions are not found.

    The particular files that are lloked after are the NCBI TAXONOMY taxdump file and
    the BRENDA JSON TAR GZ as wel as the bigg_models_metabolites.txt file.

    Args:
        path (str): The directory path where the external resource files are located.
        brenda_version (str): The version of the BRENDA database to be used.

    Raises:
        ValueError: If the specified path is not a directory.
        FileNotFoundError: If any required files are missing from the specified directory.
    """
    path = standardize_folder(path)
    if not os.path.isdir(path):
        print(
            f"ERROR: Given external resources path {path} does not seem to be a folder!"
        )
        raise ValueError
    filenames = get_files(path)

    needed_filename_data = [
        ("taxdmp.zip", "https://ftp.ncbi.nih.gov/pub/taxonomy/"),
        ("bigg_models_metabolites.txt", "http://bigg.ucsd.edu/data_access"),
    ]
    if parse_brenda:
        needed_filename_data.append(
            (
                f"brenda_{brenda_version}.json.tar.gz",
                "https://www.brenda-enzymes.org/download.php",
            )
        )
    for needed_filename, link in needed_filename_data:
        if needed_filename not in filenames:
            print(
                f"ERROR: File {needed_filename} not found in given external resources path {path}!"
            )
            print(
                "Solution: Either change the path if it is wrong, or download the file from:"
            )
            print(link)
            raise FileNotFoundError
    if "parsed_taxdmp.json.zip" not in filenames:
        parse_ncbi_taxonomy(f"{path}taxdmp.zip", f"{path}parsed_taxdmp.json")
    if "bigg_models_metabolites.json" not in filenames:
        bigg_parse_metabolites_file(
            f"{path}bigg_models_metabolites.txt", f"{path}bigg_models_metabolites.json"
        )


@validate_call(validate_return=True)
def print_model_parameter_statistics(cobrak_model: Model) -> None:
    """Prints statistics about reaction parameters (kcats and kms) in a COBRA-k model.

    This function calculates and prints statistics about the kcat and Km values
    associated with reactions in a COBRA-k model. It groups these values by their
    taxonomic distance (as indicated by references) and prints the counts for each
    distance group.  It also prints the median kcat and the median Km values for
    substrates and products separately.

    Args:
        cobrak_model: The COBRA Model object.

    Returns:
        None.  Prints statistics to the console.
    """
    substrate_kms, product_kms = get_model_kms_by_usage(cobrak_model)
    all_kms = substrate_kms + product_kms
    all_kcats = get_model_kcats(cobrak_model)

    kcats_by_taxonomy_score: dict[int, int] = {}
    kms_by_taxonomy_score: dict[int, int] = {}
    for reaction in cobrak_model.reactions.values():
        if reaction.enzyme_reaction_data is None:
            continue

        enzdata = reaction.enzyme_reaction_data
        if len(enzdata.k_cat_references) > 0:
            tax_distance = enzdata.k_cat_references[0].tax_distance
        else:
            tax_distance = -2
        if tax_distance not in kcats_by_taxonomy_score:
            kcats_by_taxonomy_score[tax_distance] = 0
        kcats_by_taxonomy_score[tax_distance] += 1

        for met_id in enzdata.k_ms:
            if (met_id in enzdata.k_m_references) and len(
                enzdata.k_m_references[met_id]
            ) > 0:
                tax_distance = enzdata.k_m_references[met_id][0].tax_distance
            else:
                tax_distance = -2
            if tax_distance not in kms_by_taxonomy_score:
                kms_by_taxonomy_score[tax_distance] = 0
            kms_by_taxonomy_score[tax_distance] += 1

    print(
        "kcats:",
        sort_dict_keys(kcats_by_taxonomy_score),
        sum(kcats_by_taxonomy_score.values()),
        len(all_kcats),
    )
    print(" ->median:", median(all_kcats))
    print(
        "kms:",
        sort_dict_keys(kms_by_taxonomy_score),
        sum(kms_by_taxonomy_score.values()),
        len(all_kms),
    )
    print(
        " ->median substrates:",
        median(substrate_kms),
        "->median products:",
        median(product_kms),
    )
    print(len(cobrak_model.reactions))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def sort_dict_keys(dictionary: dict[T, U], reverse: bool = False) -> dict[T, U]:
    """Sorts all keys in a dictionary alphabetically.

    Args:
        dictionary (dict): The dictionary to sort.

    Returns:
        dict: A new dictionary with the keys sorted alphabetically.
    """
    return dict(sorted(dictionary.items(), reverse=reverse))


@validate_call(config=ConfigDict(arbitrary_types_allowed=True), validate_return=True)
def split_list(lst: list[Any], n: PositiveInt) -> list[list[Any]]:
    """Split a list into `n` nearly equal parts.

    This function divides a given list into `n` sublists, distributing the elements as evenly as possible.

    Parameters:
    - lst (list[Any]): The list to be split.
    - n (int): The number of sublists to create.

    Returns:
    - list[list[Any]]: A list of `n` sublists, each containing a portion of the original list's elements.

    Example:
    ```
    result = _split_list([1, 2, 3, 4, 5], 3)
    # result: [[1, 2], [3, 4], [5]]
    ```

    Raises:
    - ValueError: If `n` is less than or equal to 0.
    """
    k, m = divmod(len(lst), n)
    return [lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)]
