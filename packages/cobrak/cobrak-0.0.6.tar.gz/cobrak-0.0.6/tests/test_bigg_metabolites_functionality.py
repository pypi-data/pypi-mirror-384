"""pytest tests for COBRA-k's module bigg_metabolites_functionality"""

import tempfile

from cobrak.bigg_metabolites_functionality import bigg_parse_metabolites_file


def test_bigg_parse_metabolites_file() -> None:  # noqa: D103
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_json_file:
        bigg_parse_metabolites_file(
            "examples/common_needed_external_resources/bigg_models_metabolites.txt",
            temp_json_file.name,
        )
