import json
from pathlib import Path
from typing import Any, Dict

BASE = Path(__file__).resolve().parent.parent / "schema"


async def load_standard_schema() -> Dict[str, Any]:
    """Load the standard analysis schema list.

    Returns:
        dict: {"status": "success", "data": <schema>} on success, else {"status": "error", "error_message": "..."}.
    """
    try:
        with open(BASE / "standard_analysis_schema.json", "r") as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}


async def load_analysis_schema(method: str) -> Dict[str, Any]:
    """Load an analysis-specific schema by method name.

    Args:
        method: Analysis method (ANCOVA, BINARY, TTE, MMRM).

    Returns:
        dict: {"status": "success", "data": <schema>} on success, else {"status": "error", "error_message": "..."}.
    """
    mapping = {
        "ANCOVA": "ancova1_analysis_schema.json",
        "BINARY": "binary1_analysis_schema.json",
        "TTE": "tte1_analysis_schema.json",
        "MMRM": "mmrm1_analysis_schema.json",
    }
    try:
        filename = mapping.get(method.upper(), "mmrm1_analysis_schema.json")
        with open(BASE / filename, "r") as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}
