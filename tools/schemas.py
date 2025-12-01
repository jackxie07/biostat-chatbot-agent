import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "schema"


async def load_standard_schema():
    """Return the standard analysis schema list."""
    with open(BASE / "standard_analysis_schema.json", "r") as f:
        return json.load(f)


async def load_analysis_schema(method: str):
    """
    Load the analysis-specific schema based on method name.
    """
    mapping = {
        "ANCOVA": "ancova1_analysis_schema.json",
        "BINARY": "binary1_analysis_schema.json",
        "TTE": "tte1_analysis_schema.json",
        "MMRM": "mmrm1_analysis_schema.json",
    }
    filename = mapping.get(method.upper(), "mmrm1_analysis_schema.json")
    with open(BASE / filename, "r") as f:
        return json.load(f)
