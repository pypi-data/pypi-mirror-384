"""Functions for plotting different types of data or reaction kinetics, all using matplotlib."""

import itertools
from collections.abc import Callable, Iterable, Sequence
from copy import deepcopy
from typing import Any

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
from pydantic import ConfigDict, validate_call

from cobrak.io import json_load


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def _as_numpy_array(seq: Iterable) -> np.ndarray:
    """Convert any iterable to a 1-D NumPy array (fast, safe)."""
    arr = np.asarray(seq, dtype=float)
    if arr.ndim != 1:
        raise ValueError("Each dataset must be 1-dimensional.")
    return arr


@validate_call(validate_return=True)
def _get_constant_combinations(
    n: int,
    variable_combination: tuple[int, int],
    min_values: list[float],
    max_values: list[float],
) -> list[list[float]]:
    """Generate all possible combinations of constant values for the other arguments.

    Args:
    - n: The total number of arguments.
    - variable_combination: A tuple of two variable argument indices.
    - min_values: A list of minimum possible values for each argument.
    - max_values: A list of maximum possible values for each argument.

    Returns:
    - A list of lists, where each sublist contains a combination of constant values.
    """
    constant_combinations = []
    constant_values = [
        min_values,
        [(max_values[i] - min_values[i]) / 2 + min_values[i] for i in range(n)],
        max_values,
    ]
    constant_indices = [i for i in range(n) if i not in variable_combination]
    for combination in itertools.product(range(3), repeat=len(constant_indices)):
        constant_combination = [0.0] * n
        for i, index in enumerate(constant_indices):
            constant_combination[index] = constant_values[combination[i]][index]
        constant_combinations.append(constant_combination)
    return constant_combinations


@validate_call(validate_return=True)
def distinct_colors(n: int) -> list[str]:
    """Produce *n* distinct Matplotlib colour specifications.

    Parameters
    ----------
    n : int
        Number of colours required (must be > 0).

    Returns
    -------
    List[str]
        A list of *n* colour strings.  The list is deterministic:
        calling ``distinct_colors(5)`` today and tomorrow returns
        exactly the same five colours.

    Notes
    -----
    * The first 10 colours are the Tableau palettetab:orange`` …) – the same palette that
    Matplotlib uses for its default colour cycle.
    * If ``n`` > 10 the function continues with the CSS-4 colour
    dictionary, sorted by hue (HSV) so that successive colours
    are as dissimilar as possible * All colours are returned as hex strings (e.g. ``'#1f77b4'``)
    because hex codes are universally accepted by Matplotlib.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")

    # ----------------------------------------------------------
    # 1️⃣  Tableau colours – the first 10 highly-distinct colours
    # ----------------------------------------------------------
    tableau_hex = list(mcolors.TABLEAU_COLORS.values())  # 10 entries
    if n <= len(tableau_hex):
        return tableau_hex[:n]

    # ----------------------------------------------------------
    # 2️⃣  Prepare the remaining colours (CSS-4) sorted by hue
    # ----------------------------------------------------------
    # Convert every CSS-4 colour to RGB → HSV, keep the original hex
    css_items = [
        (mcolors.rgb_to_hsv(mcolors.to_rgb(hexcol)), hexcol)
        for hexcol in mcolors.CSS4_COLORS.values()
    ]
    # Sort by hue (the first component of HSV)
    css_items.sort(key=lambda pair: pair[0][0])

    # Extract the sorted hex strings
    css_sorted_hex = [hexcol for _, hexcol in css_items]

    # ----------------------------------------------------------
    # 3️⃣  Concatenate Tableau + sorted CSS-4 and slice to *n*
    # ----------------------------------------------------------
    all_colours = tableau_hex + css_sorted_hex
    return all_colours[:n]


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def dual_axis_plot(
    xpoints: list[float],
    leftaxis_ypoints_list: list[list[float]],
    rightaxis_ypoints_list: list[list[float]],
    xaxis_caption: str = "",
    leftaxis_caption: str = "",
    rightaxis_caption: str = "",
    leftaxis_colors: list[str] = [],
    rightaxis_colors: list[str] = [],
    leftaxis_titles: list[str] = [],
    rightaxis_titles: list[str] = [],
    extrapoints: list[tuple[float, float, bool, str, str, str, float]] = [],
    has_legend: bool = True,
    legend_direction: str = "",
    legend_position: tuple[Any, ...] = (),
    is_leftaxis_logarithmic: bool = False,
    is_rightaxis_logarithmic: bool = False,
    point_style: str = "",
    line_style: str = "-",
    max_digits_after_comma: int = 4,
    savepath: str = "",
    left_ylim: None | tuple[float, float] = None,
    right_ylim: None | tuple[float, float] = None,
    xlim: None | tuple[float, float] = None,
    left_axis_in_front: bool = True,
    left_legend_position: list[int] = [],
    right_legend_position: list[int] = [],
    figure_size_inches: None | tuple[float, float] = None,
    special_figure_mode: bool = False,
    axistitle_labelsize: float = 14,
    axisticks_labelsize: float = 13,
    legend_labelsize: float = 13,
    extrahlines: list[tuple[float, str, str, str | None]] = [],
) -> None:
    """Creates a plot with a dual Y-axis.

    Args:
        xpoints (list[float]): X-axis data points.
        leftaxis_ypoints_list (list[list[float]]): List of Y-axis data points for the left axis.
        rightaxis_ypoints_list (list[list[float]]): List of Y-axis data points for the right axis.
        xaxis_caption (str, optional): X-axis caption. Defaults to "".
        leftaxis_caption (str, optional): Left Y-axis caption. Defaults to "".
        rightaxis_caption (str, optional): Right Y-axis caption. Defaults to "".
        leftaxis_colors (list[str], optional): Colors for left axis lines. Defaults to [].
        rightaxis_colors (list[str], optional): Colors for right axis lines. Defaults to [].
        leftaxis_titles (list[str], optional): Legend titles for left axis lines. Defaults to [].
        rightaxis_titles (list[str], optional): Legend titles for right axis lines. Defaults to [].
        extrapoints (list[tuple[float, float, bool, str, str, str, float]], optional): List of single points,
            described by tuples with the content [x, y, is_left_axis, color, marker, label, yerr]. If yerr=0,
            no error bar is drawn at all. Defaults to [].
        has_legend (bool, optional): Whether to show the legend. Defaults to True.
        legend_direction (str, optional): Legend direction. Defaults to "".
        legend_position (tuple[float, float], optional): Legend position. Defaults to ().
        is_leftaxis_logarithmic (bool, optional): Whether to use a logarithmic scale for the left axis. Defaults to False.
        is_rightaxis_logarithmic (bool, optional): Whether to use a logarithmic scale for the right axis. Defaults to False.
        point_style (str, optional): Style for points. Defaults to "".
        line_style (str, optional): Style for lines. Defaults to "-".
        max_digits_after_comma (int, optional): Max digits after comma shown. Defaults to 4.
        savepath (str): If given, the plot is not shown but saved at the given path. Defaults to ""

    Returns:
        None (displays the plot)
    """

    fig, ax1 = plt.subplots()
    if figure_size_inches is not None:
        fig.set_size_inches(figure_size_inches[0], figure_size_inches[1])

    # Left Axis Plotting
    for (y, color, linestyle, label) in extrahlines:
        ax1.axhline(
            y=y,
            color=color,
            linestyle=linestyle,
            label=label,
        )

    for i, ypoints in enumerate(leftaxis_ypoints_list):
        color = leftaxis_colors[i] if leftaxis_colors else None
        title = leftaxis_titles[i] if leftaxis_titles else None
        ax1.plot(
            xpoints,
            ypoints,
            color=color,
            linestyle=line_style,
            marker=point_style,
            label=title,
        )

    ax1.set_xlabel(xaxis_caption, fontsize=axistitle_labelsize)
    ax1.set_ylabel(leftaxis_caption, fontsize=axistitle_labelsize)
    if is_leftaxis_logarithmic:
        ax1.set_yscale("log")
    if left_ylim is not None:
        ax1.set_ylim(left_ylim[0], left_ylim[1])

    plt.xticks(fontsize=axisticks_labelsize)
    plt.yticks(fontsize=axisticks_labelsize)

    # Right Axis Plotting
    if len(rightaxis_ypoints_list) > 0:
        ax2 = ax1.twinx()
        for i, ypoints in enumerate(rightaxis_ypoints_list):
            color = rightaxis_colors[i] if rightaxis_colors else None
            title = rightaxis_titles[i] if rightaxis_titles else None
            ax2.plot(
                xpoints,
                ypoints,
                color=color,
                linestyle=line_style,
                marker=point_style,
                label=title,
            )

        ax2.set_ylabel(rightaxis_caption, fontsize=axistitle_labelsize)
        if is_rightaxis_logarithmic:
            ax2.set_yscale("log")
        if right_ylim is not None:
            ax2.set_ylim(right_ylim[0], right_ylim[1])

        if left_axis_in_front:
            ax1.set_zorder(ax2.get_zorder() + 1)
            ax1.patch.set_visible(False)

    if xlim is not None:
        ax1.set_xlim(xlim[0], xlim[1])

    for i, extrapoint in enumerate(extrapoints):
        axis = ax1 if extrapoint[2] else ax2
        if extrapoint[6] != 0.0:
            axis.errorbar(
                extrapoint[0],
                extrapoint[1],
                yerr=extrapoint[6],
                ecolor=extrapoint[3],
                capsize=5,
                linestyle="",
                color=extrapoint[3],
                marker=extrapoint[4],
                label=extrapoint[5],
            )
        else:
            axis.plot(
                extrapoint[0],
                extrapoint[1],
                linestyle="",
                color=extrapoint[3],
                marker=extrapoint[4],
                label=extrapoint[5],
            )

    # Legend
    if has_legend:
        handles, labels = ax1.get_legend_handles_labels()
        if len(rightaxis_ypoints_list) > 0:
            handles2, labels2 = ax2.get_legend_handles_labels()

            if left_legend_position != []:
                oldhandles, oldlabels = deepcopy(handles), deepcopy(labels)
                for i, left_legend_position in enumerate(left_legend_position):
                    handles[left_legend_position] = oldhandles[i]
                    labels[left_legend_position] = oldlabels[i]

            if right_legend_position != []:
                oldhandles2, oldlabels2 = deepcopy(handles2), deepcopy(labels2)
                for i, right_legend_position in enumerate(right_legend_position):
                    handles2[right_legend_position] = oldhandles2[i]
                    labels2[right_legend_position] = oldlabels2[i]
            if special_figure_mode:
                # Just for COBRA-k's initial publication :-)
                # del handles[1]
                # del labels[1]
                # handles2.append(oldhandles[-2])
                # labels2.append(oldlabels[-2])
                pass

            handles = handles + handles2
            labels = labels + labels2
        extraargs = {"loc": legend_position} if legend_position != () else {}
        if legend_direction:
            extraargs["loc"] = legend_direction
        plt.legend(
            handles,
            labels,
            bbox_to_anchor=(0.5, 0.5)
            if not legend_position and not legend_direction
            else None,
            fontsize=legend_labelsize,
            **extraargs,
        )

    plt.xticks(fontsize=axisticks_labelsize)
    plt.yticks(fontsize=axisticks_labelsize)

    # Format axis ticks
    ax1.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:.{max_digits_after_comma}f}")
    )
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:.{max_digits_after_comma}f}")
    )
    if len(rightaxis_ypoints_list) > 0:
        ax2.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x:.{max_digits_after_comma}f}")
        )

    plt.tight_layout()  # Adjust layout to prevent labels from overlapping

    if not savepath:
        plt.show()
    else:
        plt.savefig(savepath, dpi=300)

    # Close the plot to free up memory
    plt.close()


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def plot_combinations(
    func: Callable[[list[float]], float],
    min_values: list[float],
    max_values: list[float],
    num_subplots_per_window: int = 18,
    num_subplots_per_row: int = 6,
) -> None:
    """Plot all unique combinations of 2 variable arguments and constant values for the other arguments.

    The plot is a scatter plot with different colors for each category in the hue column. The x-axis represents the x-data,
    the y-axis represents the y-data, and the hue axis represents the category.

    The plot has the following features:

    * A title at the top of the plot with the specified title.
    * Labels for the x-axis and y-axis with the specified labels.
    * A legend on the right side of the plot with the specified hue label.
    * Different colors for each category in the hue column, specified by the palette.
    * A scatter plot with points representing the data.

    Example usage:
    from cobrak.plotting import plot_combinations
    min_values = [-1.0, 0.0, 0.0]
    max_values = [10.0, 5.0, 10.0]
    def example_func(args: List[float]) -> float:
       return args[0] + args[1] + args[2]
    plot_combinations(example_func, min_values, max_values)

    Args:
    - func: The function to be plotted. It takes a list of floats and returns a float.
    - min_values: A list of minimum possible values for each argument.
    - max_values: A list of maximum possible values for each argument.
    - num_subplots_per_window: The maximum number of subplots per window. Defaults to 18.
    - num_subplots_per_row: The maximum number of subplots per row in a window. Defaults to 6.

    Returns:
    - None
    """

    # Generate all possible combinations of 2 variable arguments
    variable_combinations = []
    for i in range(len(min_values)):
        for j in range(i + 1, len(min_values)):
            variable_combinations.append((i, j))

    # Generate all unique combinations of variable and constant arguments
    combinations = []
    for variable_combination in variable_combinations:
        constant_combinations = _get_constant_combinations(
            len(min_values), variable_combination, min_values, max_values
        )
        for constant_combination in constant_combinations:
            combinations.append((variable_combination, constant_combination))

    # Plot each combination
    num_windows = int(np.ceil(len(combinations) / num_subplots_per_window))
    for window_index in range(num_windows):
        num_subplots = min(
            num_subplots_per_window,
            len(combinations) - window_index * num_subplots_per_window,
        )
        num_rows = int(np.ceil(num_subplots / num_subplots_per_row))
        _, axs = plt.subplots(
            num_rows,
            num_subplots_per_row,
            figsize=(20, 5 * num_rows),
            subplot_kw={"projection": "3d"},
        )
        if num_subplots_per_row == 1:
            axs = [[ax] for ax in axs]
        elif num_rows == 1:
            axs = [axs]
        else:
            axs = [list(axs_row) for axs_row in axs]

        z_mins = {}
        z_maxs = {}
        for combination in combinations[
            window_index * num_subplots_per_window : (window_index + 1)
            * num_subplots_per_window
        ]:
            variable_combination, constant_combination = combination
            if variable_combination not in z_mins:
                z_mins[variable_combination] = float("inf")
                z_maxs[variable_combination] = float("-inf")
            x = np.linspace(
                min_values[variable_combination[0]],
                max_values[variable_combination[0]],
                100,
            )
            y = np.linspace(
                min_values[variable_combination[1]],
                max_values[variable_combination[1]],
                100,
            )
            X, Y = np.meshgrid(x, y)
            Z = np.zeros(X.shape)
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    args = [
                        (
                            X[i, j]
                            if k == variable_combination[0]
                            else (
                                Y[i, j]
                                if k == variable_combination[1]
                                else constant_combination[k]
                            )
                        )
                        for k in range(len(min_values))
                    ]
                    Z[i, j] = func(args)
            z_mins[variable_combination] = min(z_mins[variable_combination], np.min(Z))  # type: ignore
            z_maxs[variable_combination] = max(z_maxs[variable_combination], np.max(Z))  # type: ignore

        for subplot_index, combination in enumerate(
            combinations[
                window_index * num_subplots_per_window : (window_index + 1)
                * num_subplots_per_window
            ]
        ):
            variable_combination, constant_combination = combination
            x = np.linspace(
                min_values[variable_combination[0]],
                max_values[variable_combination[0]],
                100,
            )
            y = np.linspace(
                min_values[variable_combination[1]],
                max_values[variable_combination[1]],
                100,
            )
            X, Y = np.meshgrid(x, y)
            Z = np.zeros(X.shape)
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    args = [
                        (
                            X[i, j]
                            if k == variable_combination[0]
                            else (
                                Y[i, j]
                                if k == variable_combination[1]
                                else constant_combination[k]
                            )
                        )
                        for k in range(len(min_values))
                    ]
                    Z[i, j] = func(args)

            row_index = subplot_index // num_subplots_per_row
            col_index = subplot_index % num_subplots_per_row

            axs[row_index][col_index].plot_surface(
                X, Y, Z, cmap="viridis", edgecolor="none"
            )
            axs[row_index][col_index].set_xlabel(f"Argument {variable_combination[0]}")
            axs[row_index][col_index].set_ylabel(f"Argument {variable_combination[1]}")
            axs[row_index][col_index].set_zlim(
                z_mins[variable_combination], z_maxs[variable_combination]
            )

            constant_title = ", ".join(
                [
                    f"{i}: {constant_combination[i]}"
                    for i in range(len(min_values))
                    if i not in variable_combination
                ]
            )
            axs[row_index][col_index].set_title(
                (
                    f"Variable: {variable_combination[0]}, {variable_combination[1]}\n"
                    f"Constant: {constant_title}"
                    if constant_title
                    else f"Variable: {variable_combination[0]}, {variable_combination[1]}"
                ),
                fontsize=8,
            )

            # Hide empty plots
            if subplot_index >= num_subplots:
                axs[row_index][col_index].axis("off")

        plt.tight_layout()
        plt.show()


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def plot_range_bars(
    data_captions: list[str],
    data_labels: list[str],
    data_ranges: list[list[tuple[float, float]]],
    data_colors: list[str],
    *,
    cap_len: float = 0.2,
    line_width: float = 3.0,
    figsize: tuple[float, float] = (10, 6),
    title: str = "Range.Bar Plot",
    ylabel: str = "Label",
    xlabel: str = "Value",
    ax: plt.Axes | None = None,
    highlight_means: list[bool] | None = None,
    log_y: bool = False,
    legend_pos: str | None = None,
    marker_size: float = 80,
    title_labelsize: float = 16,
    axes_labelsize: float = 13,
    ticks_labelsize: float = 13,
    legend_labelsize: float = 11,
    legend_bbox_to_anchor: None | tuple[float, float] = None,
    ylim: None | tuple[float, float] = None,
) -> plt.Axes:
    """Plot vertical range bars with categorical labels on the x‑axis.

    Parameters
    ----------
    data_captions: list[str]
        Labels for the *legend*. List length must equal the one from e.g. data_colors.
    data_labels : list[str]
        Labels for the x axis.  The same strings are also
        used as the x‑axis tick labels after alphabetical sorting.
    data_ranges : list[list[tuple[float, float]]]
        Outer list length = number of groups (must equal ``len(data_colors)``).
        Each inner list must have the same length as ``data_labels``.
        ``(low, high)`` defines the numeric range for the corresponding label.
    data_colors : list[str]
        Colour for each group; length must match the outer dimension of
        ``data_ranges``.
    cap_len : float, optional
        Half‑width of the horizontal caps at each end of a bar (default 0.2).
    line_width : float, optional
        Thickness of the vertical bars and caps (default 3.0).
    figsize : tuple[float, float], optional
        Figure size passed to ``plt.subplots`` (default (10, 6)).
    title, ylabel, xlabel : str, optional
        Plot title and axis labels.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on; if ``None`` a new figure and axes are created.
    highlight_means : list[bool] | None, optional
        ``True`` for a group means that the mean of each range
        ``(low+high)/2`` is highlighted with a larger circular marker.
        Length must equal ``len(data_ranges)``.  If ``None`` no means are
        highlighted.
    log_y : bool, optional
        If ``True`` the y‑axis is set to a logarithmic scale.
    legend_pos: str | None, optional.
        If not ```None```, the given matplotlib legend position is used.

    Returns
    -------
    matplotlib.axes.Axes
        The axes containing the generated plot.

    Raises
    ------
    ValueError
        If the lengths of the input sequences are inconsistent.
    """
    # ------------------------------------------------------------------ #
    # 1️⃣  Sanity checks
    # ------------------------------------------------------------------ #
    n_groups = len(data_ranges)

    if n_groups != len(data_colors):
        raise ValueError("len(data_colors) must equal the outer length of data_ranges")
    if any(len(inner) != len(data_labels) for inner in data_ranges):
        raise ValueError(
            "Every inner list in data_ranges must have the same length as data_labels"
        )
    if highlight_means is not None and len(highlight_means) != n_groups:
        raise ValueError(
            "highlight_means must be ``None`` or a list with length equal to the number of groups"
        )

    # ------------------------------------------------------------------ #
    # 2️⃣  Alphabetical ordering of the categorical labels (x‑axis)
    # ------------------------------------------------------------------ #
    sorted_idx = sorted(range(len(data_labels)), key=lambda i: data_labels[i])
    sorted_labels = [data_labels[i] for i in sorted_idx]
    # reorder each group’s ranges to match the sorted label order
    sorted_ranges = [[grp[i] for i in sorted_idx] for grp in data_ranges]

    # ------------------------------------------------------------------ #
    # 3️⃣  Figure / Axes handling
    # ------------------------------------------------------------------ #
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    x_pos = range(len(sorted_labels))

    # ------------------------------------------------------------------ #
    # 4️⃣  Plot each group
    # ------------------------------------------------------------------ #
    for grp_idx, (grp_ranges, colour) in enumerate(zip(sorted_ranges, data_colors)):
        lows = [rng[0] for rng in grp_ranges]
        highs = [rng[1] for rng in grp_ranges]

        # vertical range bars
        ax.vlines(
            x=x_pos,
            ymin=lows,
            ymax=highs,
            color=colour,
            linewidth=line_width,
        )
        # caps – low end
        ax.hlines(
            y=lows,
            xmin=[xp - cap_len / 2 for xp in x_pos],
            xmax=[xp + cap_len / 2 for xp in x_pos],
            color=colour,
            linewidth=line_width,
        )
        # caps – high end
        ax.hlines(
            y=highs,
            xmin=[xp - cap_len / 2 for xp in x_pos],
            xmax=[xp + cap_len / 2 for xp in x_pos],
            color=colour,
            linewidth=line_width,
        )

        # ------------------------------------------------------------------
        # 4️⃣️⃣  Optional mean highlighting
        # ------------------------------------------------------------------
        if highlight_means and highlight_means[grp_idx]:
            means = [(low + high) / 2 for low, high in zip(lows, highs)]
            ax.scatter(
                x=list(x_pos),
                y=means,
                color=colour,
                edgecolor="k",
                zorder=5,
                s=marker_size,
                marker="_",
                linewidth=1.5,
                label="_mean",  # dummy label – we will build the legend ourselves
            )

    # ------------------------------------------------------------------ #
    # 5️⃣  Cosmetics
    # ------------------------------------------------------------------ #
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(sorted_labels, rotation=45, ha="right")
    ax.set_xlabel(xlabel, fontsize=axes_labelsize)
    ax.set_ylabel(ylabel, fontsize=axes_labelsize)
    ax.set_title(title, loc="left", fontweight="bold", fontsize=title_labelsize)
    ax.yaxis.grid(True, which="both", linestyle="--", alpha=0.5)
    if ylim:
        ax.set_ylim(ylim[0], ylim[1])
    ax.tick_params(axis="x", labelsize=ticks_labelsize)
    ax.tick_params(axis="y", labelsize=ticks_labelsize)

    if log_y:
        ax.set_yscale("log")

    # ------------------------------------------------------------------ #
    # 6️⃣  Legend – use *data_labels* (one entry per group) with the supplied colours
    # ------------------------------------------------------------------ #
    legend_handles = [
        Line2D([0], [0], color=col, lw=line_width, label=lbl)
        for lbl, col in zip(data_captions, data_colors)
    ]
    ax.legend(
        handles=legend_handles,
        loc="best" if legend_pos is None else legend_pos,
        fontsize=legend_labelsize,
        bbox_to_anchor=legend_bbox_to_anchor
    )
    ax.margins(x=0.01)

    plt.tight_layout()
    return ax


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def multi_step_histogram(
    data: list[list[float]],
    *,
    bins: int | Sequence[float] | str = 10,
    range_: tuple[float, float] | None = None,
    density: bool = False,
    labels: Sequence[str] | None = None,
    colors: Sequence[str] | None = None,
    linewidth: float = 1.5,
    alpha: float = 1.0,
    linestyle: str = "-",
    title: str | None = None,
    xlabel: str | None = "Value",
    ylabel: str | None = None,
    legend_loc: str | None = "best",
    ax: plt.Axes | None = None,
    logmode: bool = False,
    **hist_kwargs,  # noqa: ANN003
) -> plt.Axes:
    """Plot several 1-D data sets as *step* histograms on a single Axes.

    Parameters
    ----------
    data : sequence of iterables
        Each element is a collection of numbers (list, np.ndarray, pd.Series …).
    bins : int, sequence of scalars, or str, default 10
        Passed straight to ``np.histogram`` / ``plt.hist``.
        Use e.g. ``'auto'`` or an explicit array of bin edges for full control.
    range_ : (float, float), optional
        Lower and upper range_ of the bins.  If ``None`` the range_ is
        inferred from the data.
    density : bool, default False
        If True, the histogram is normalized to form a probability density,
        i.e. the integral of the histogram is 1.
    labels : sequence of str, optional
        Human-readable names for the data sets.  If omitted, generic names
        ``Dataset 0``, ``Dataset 1`` … are used.
    colors : sequence of str, optional
        Matplotlib colour specifications.  If omitted, the default colour cycle
        is used.
    linewidth : float, default 1.5
        Width of the step lines.
    alpha : float in [0,1], default 1.0
        Transparency of the lines.
    linestyle : str, default '-'
        Any valid matplotlib line style (``'-'``, ``'--'``, ``':'`` …).
    title, xlabel, ylabel : str, optional
        Axis titles.
    legend_loc : str or None, default 'best'
        Location of the legend; set to ``None`` to suppress the legend.
    ax : matplotlib.axes.Axes, optional
        Provide an existing Axes to plot into; otherwise a new figure/axes
        pair is created.
    **hist_kwargs
        Additional keyword arguments forwarded to ``plt.hist`` (e.g.
        ``log=True`` for a log-scale y-axis).

    Returns
    -------
    matplotlib.axes.Axes
        The Axes object containing the plot (useful for further tweaking).

    Example
    -------
    import numpy as np
    from cobrak.plotting import multi_step_histogram
    rng = np.random.default_rng()
    d1 = rng.normal(size=1000)
    d2 = rng.exponential(scale=2, size=1000)
    multi_step_histogram([d1, d2],
                        bins=40,
                        density=True,
                        labels=['Normal', 'Exp'],
                        colors=['tab:blue', 'tab:red'],
                        title='Density step-histograms')
    """

    def _fmt(val: Any, _: Any) -> str:  # noqa: ANN401
        return f"{np.exp(val):.0e}"

    # ------------------------------------------------------------------
    # 1️⃣  Prepare the Axes
    # ------------------------------------------------------------------
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.figure

    # ------------------------------------------------------------------
    # 2️⃣  Normalise input arguments
    # ------------------------------------------------------------------
    n_sets = len(data)
    if labels is None:
        labels = [f"Dataset {i}" for i in range(n_sets)]
    if len(labels) != n_sets:
        raise ValueError("Length of `labels` must match number of data sets.")

    if colors is not None and len(colors) != n_sets:
        raise ValueError("Length of `colors` must match number of data sets.")
    if colors is None:
        colors = distinct_colors(n_sets)

    # ------------------------------------------------------------------
    # 3️⃣  Plot each histogram as a step line
    # ------------------------------------------------------------------
    for idx, (ds, lbl) in enumerate(zip(data, labels)):
        arr = _as_numpy_array(ds)
        if logmode:
            arr = np.log(arr)
        # plt.hist with `histtype='step'` draws exactly what we need.
        # We forward any extra **hist_kwargs** (e.g. log=True) to give the user
        # full flexibility.
        counts, bin_edges, _ = ax.hist(
            arr,
            bins=bins,
            range=range_,
            density=density,
            histtype="step",
            label=lbl,
            color=None if colors is None else colors[idx],
            linewidth=linewidth,
            alpha=alpha,
            linestyle=linestyle,
            **hist_kwargs,
        )

        # --------------------------------------------------------------
        #  Median line – stops at the histogram step
        # --------------------------------------------------------------
        med = np.median(arr)  # median of the data set
        # Find the bin that contains the median
        bin_idx = np.searchsorted(bin_edges, med, side="right") - 1
        # Guard against edge-cases (median exactly on the rightmost edge)
        bin_idx = np.clip(bin_idx, 0, len(counts) - 1)

        # Height of the histogram at the median (count or density)
        med_height = counts[bin_idx]

        # Draw a vertical line from y=0 up to the histogram line
        ax.vlines(
            med,
            0,
            med_height,
            colors=colors[idx] if colors is not None else None,
            linestyles="dashed",
            linewidth=1.5,
        )

    # ------------------------------------------------------------------
    # 4️⃣  Tidy up the figure
    # ------------------------------------------------------------------
    if title:
        ax.set_title(title, fontsize=14, pad=12)

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)

    # If the user did not provide a custom ylabel we choose a sensible default.
    if ylabel is None:
        ylabel = "Density" if density else "Count"
    ax.set_ylabel(ylabel, fontsize=12)

    if legend_loc is not None:
        ax.legend(loc=legend_loc, fontsize=10)

    ax.grid(True, which="both", ls=":", linewidth=0.5, alpha=0.7)

    # Tight layout so labels are not clipped.
    fig.tight_layout()

    if logmode:
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(_fmt))

    plt.show()

    return ax


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def plot_objvalue_evolution(
    json_path: str,
    output_path: str,
    ylabel: str = "Objective value",
    objvalue_multiplicator: float = -1.0,
    with_legend: bool = False,
    precision: int = 4,
) -> None:
    """Plots the evolution of the objective value over computational time.

    Args:
        json_path (str): Path to the JSON file containing the data.
        output_path (str): Path to save the plot.
        ylabel (str, optional): Label for the Y-axis. Defaults to "Objective value".
        objvalue_multiplicator (float, optional): Multiplier to apply to the objective value. Defaults to -1.0.
        with_legend (bool, optional): Whether to display the legend. Defaults to False.
        precision (int, optional): The number of decimal places to display on the Y-axis. Defaults to 4.

    Returns:
        None. Saves the plot to the specified output path.
    """

    def format_decimal(x, _) -> str:  # noqa: ANN001
        return f"{x:.{precision}f}"  # Use the specified precision

    # Load data from JSON file
    data = json_load(json_path, Any)

    # Extract timepoints
    timepoints = tuple(float(key) for key in data)

    # Initialize objvalues list
    objvalues = [[]]

    # Populate objvalues list
    for values in data.values():
        objvalues[0].append(objvalue_multiplicator * values[0])

    plt.clf()
    plt.cla()
    plt.plot(timepoints, objvalues[0], linestyle="-", marker=None, label="Best value")

    # Customize the plot
    plt.xlabel("Computational Time [s]")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} Evolution Over Time")
    if with_legend:
        plt.legend()

    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_decimal))

    # Save the plot
    plt.savefig(output_path)

    # Close the plot to free up memory
    plt.close()


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def plot_variabilities(
    variabilities: list[list[tuple[float, float, float]]],
    variability_names: list[str],
    variability_titles: list[str],
    colors: list[str],
    xlabel: str = "",
    ylabel: str = "",
    yscale: str = "log",
    plot_mean: bool = True,
    save_path: str | None = None,
) -> None:
    """Plots the mean values and whisker bars for multiple variabilities.

    This function generates a plot where each variability is represented by a series of points (triangles) and whisker bars.
    Each point (if plot_mean==True) represents the mean value of a data point in the variability, and the whisker bars represent the lower and upper bounds.
    The variabilities are grouped together for each data point, with a space between each group to clearly distinguish them.

    Parameters:
    -----------
    variabilities : List[List[Tuple[float, float, float]]]
    A list of lists, where each inner list represents a variability. Each tuple in the inner list contains
    (lower_bound, upper_bound, mean_value) for each data point in the variability.

    variability_names : List[str]
    A list of strings representing the names of the variabilities.

    colors : List[str]
    A list of strings representing the colors for each variability, e.g. using names from https://matplotlib.org/stable/gallery/color/named_colors.html

    plot_mean : bool, optional
    If True, the mean value is plotted as a triangle. If False, only the whisker bars are plotted. Default is True.

    save_path : str, optional
    The file path where the plot should be saved. If None, the plot is displayed. Default is None.

    Returns:
    --------
    None
    The function either displays the plot or saves it to the specified path.

    Example:
    --------
    from cobrak.plotting import plot_variabilities
    in_vivo = [(1.0, 3.0, 2.0), (2.0, 4.0, 3.0), (3.0, 5.0, 4.0)]
    in_silico = [(1.5, 3.5, 2.5), (2.5, 4.5, 3.5), (3.5, 5.5, 4.5)]
    another_variability = [(1.2, 3.2, 2.2), (2.2, 4.2, 3.2), (3.2, 5.2, 4.2)]
    variabilities = [in_vivo, in_silico, another_variability]
    variability_names = ['in_vivo', 'in_silico', 'another_variability']
    colors = ['blue', 'orange', 'green']
    plot_variabilities(variabilities, variability_names, colors)
    plot_variabilities(variabilities, variability_names, colors, plot_mean=False)
    plot_variabilities(variabilities, variability_names, colors, save_path='plot.png')
    """
    # Number of variabilities
    n = len(variabilities[0])
    num_variabilities = len(variabilities)

    # Create a figure and axis
    _, ax = plt.subplots()

    # Define the positions for the groups
    positions = [
        list(
            range(
                i * (num_variabilities + 1),
                i * (num_variabilities + 1) + num_variabilities,
            )
        )
        for i in range(n)
    ]

    # Plot each variability
    for i, (pos_group, variability) in enumerate(zip(positions, zip(*variabilities))):
        for j, (pos, (lower, upper, mean)) in enumerate(zip(pos_group, variability)):
            if plot_mean:
                ax.errorbar(
                    pos,
                    mean,
                    yerr=[[mean - lower], [upper - mean]],
                    fmt="o",
                    capsize=5,
                    color=colors[j],
                    ecolor=colors[j],
                    label=variability_titles[j] if i == 0 else "",
                )
            else:
                ax.errorbar(
                    pos,
                    mean,
                    yerr=[[mean - lower], [upper - mean]],
                    fmt="none",
                    capsize=5,
                    ecolor=colors[j],
                    label=variability_titles[j] if i == 0 else "",
                )

    # Calculate midpoints between groups for vertical lines
    for i in range(len(positions) - 1):
        # Get the end of the current group and the start of the next group
        current_group_end = positions[i][-1]
        next_group_start = positions[i + 1][0]
        # Calculate the midpoint
        midpoint = (current_group_end + next_group_start) / 2
        # Draw a thin vertical black line at the midpoint
        ax.axvline(x=midpoint, color="black", linestyle="-", linewidth=0.5, alpha=0.7)

    # Set the x-axis labels
    ax.set_xticks([pos[0] + (num_variabilities - 1) / 2 for pos in positions])
    ax.set_xticklabels(variability_names)  # [f"Exp {i+1}" for i in range(n)])

    # Add labels and title
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title("Comparison of Variabilities")
    ax.set_yscale(yscale)

    # Add legend
    ax.legend()

    # Save or show the plot
    if save_path is not None:
        plt.savefig(save_path)
    else:
        plt.show()


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def scatterplot_with_labels(
    x_data: list[tuple[float, float, float]],
    y_data: list[tuple[float, float, float]],
    labels: list[str],
    x_label: str = None,
    y_label: str = None,
    y_log: bool = True,
    x_log: bool = True,
    add_labels: bool = False,
    identical_axis_lims: bool = True,
    xlim_overwrite: None | tuple[float, float] = None,
    ylim_overwrite: None | tuple[float, float] = None,
    ax: plt.Axes = None,
    save_path: str = None,
    title: str | None = None,
    extratext: str | None = None,
    x_labelsize: float = 13,
    y_labelsize: float = 13,
    major_tick_labelsize: float = 13,
    minor_tick_labelsize: float = 10,
    legend_labelsize: float = 13,  # noqa: ARG001
    title_labelsize: float = 16,
    extratext_labelsize: float = 14,
    label_fontsize: float = 13,
    labelcoords: tuple[float, float] = (0, 10),
) -> plt.Axes:
    """Generates a scatter plot with error bars and optional point labels.

    Can be used standalone ("one-off" plot with plt.show()), or for subplotting by passing an Axes object.
    Optionally saves the figure if save_path is provided.

    Parameters
    ----------
    x_data : list[tuple[float, float, float]]
        Each tuple is (lower bound, upper bound, drawn value) for x.
    y_data : list[tuple[float, float, float]]
        Each tuple is (lower bound, upper bound, drawn value) for y.
    labels : list[str]
        Labels for each point (used if add_labels is True).
    x_label : str, optional
        X-axis label.
    y_label : str, optional
        Y-axis label.
    y_log : bool, default True
        Use log scale for y-axis.
    x_log : bool, default True
        Use log scale for x-axis.
    add_labels : bool, default False
        Annotate points with corresponding label.
    identical_axis_lims : bool, default True
        Make x and y axis limits identical and auto-scale them.
    ax : matplotlib.axes.Axes, optional
        If provided, plot is drawn on this Axes (for subplotting).
    save_path : str, optional
        If provided and `ax` is None (standalone plotting), save the figure at this path instead of showing.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axis object containing the plot.
    """
    # Calculate midpoints and error sizes for x and y coordinates
    x_drawn = [x[2] for x in x_data]
    x_low = [x[0] for x in x_data]
    x_high = [x[1] for x in x_data]
    x_err_low = [x_drawn[i] - x_low[i] for i in range(len(x_data))]
    x_err_high = [x_high[i] - x_drawn[i] for i in range(len(x_data))]

    y_drawn = [y[2] for y in y_data]
    y_low = [y[0] for y in y_data]
    y_high = [y[1] for y in y_data]
    y_err_low = [y_drawn[i] - y_low[i] for i in range(len(y_data))]
    y_err_high = [y_high[i] - y_drawn[i] for i in range(len(y_data))]

    n_points = len(x_drawn)
    colors = get_cmap("viridis")(np.linspace(0, 1, n_points))

    _created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        _created_fig = True

    # Plot each point individually to assign different colors
    for i in range(n_points):
        ax.errorbar(
            x_drawn[i],
            y_drawn[i],
            xerr=[[x_err_low[i]], [x_err_high[i]]],
            yerr=[[y_err_low[i]], [y_err_high[i]]],
            fmt="o",
            markersize=7,
            color=colors[i],
            capsize=4,
            capthick=2,
            elinewidth=2,
        )

    # Add labels to each point
    if add_labels:
        for i, (xi, yi) in enumerate(zip(x_drawn, y_drawn)):
            ax.annotate(
                labels[i],
                (xi, yi),
                textcoords="offset points",
                xytext=labelcoords,
                ha="center",
                fontsize=label_fontsize,
            )

    # Axis limits & unity line
    all_x_values = [x_datapoint[0] for x_datapoint in x_data] + [
        x_datapoint[1] for x_datapoint in x_data
    ]
    all_y_values = [y_datapoint[0] for y_datapoint in y_data] + [
        y_datapoint[1] for y_datapoint in y_data
    ]

    min_val = min(*all_y_values, *all_x_values) * 0.99
    max_val = max(*all_y_values, *all_x_values) * 1.2

    if identical_axis_lims:
        ax.set_xlim(min_val, max_val)
        ax.set_ylim(min_val, max_val)

    if xlim_overwrite is not None:
        ax.set_xlim(xlim_overwrite[0], xlim_overwrite[1])
    if ylim_overwrite is not None:
        ax.set_ylim(ylim_overwrite[0], ylim_overwrite[1])

    x_unity = np.linspace(0, max_val * 100, 10)
    y_unity = x_unity
    ax.plot(x_unity, y_unity, "-", color="black", linewidth=1)

    if y_log:
        ax.set_yscale("log")
    if x_log:
        ax.set_xscale("log")

    if x_label:
        ax.set_xlabel(x_label, fontsize=x_labelsize)
    if y_label:
        ax.set_ylabel(y_label, fontsize=y_labelsize)

    if title is not None:
        ax.set_title(title, loc="left", fontweight="bold", fontsize=title_labelsize)

    if extratext:
        ax.text(
            0.025,
            0.975,
            extratext,
            horizontalalignment="left",
            verticalalignment="top",
            transform=ax.transAxes,
            fontsize=extratext_labelsize,
            fontweight="bold",
        )

    ax.grid(True)

    ax.tick_params(axis="both", which="major", labelsize=major_tick_labelsize)
    ax.tick_params(axis="both", which="minor", labelsize=minor_tick_labelsize)
    ax.yaxis.set_major_locator(ax.xaxis.get_major_locator())

    if _created_fig:
        plt.tight_layout()
        if save_path is not None:
            plt.savefig(save_path)
        else:
            plt.show()
        plt.close(fig)
    return ax
