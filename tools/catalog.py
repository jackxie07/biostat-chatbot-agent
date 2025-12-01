import json
from pathlib import Path
from typing import Any, Dict, List

BASE = Path(__file__).resolve().parent.parent / "schema"


async def _load_json(name: str) -> List[Dict[str, Any]]:
    with open(BASE / name, "r") as f:
        return json.load(f)


async def list_options(param: str):
    """
    Return allowed options for the given parameter.
    """
    param = param.lower()
    if param == "endpoint":
        return await _load_json("dataset_endpoint_schema.json")
    if param == "population":
        return await _load_json("dataset_population_schema.json")
    if param == "responsevariable":
        return await _load_json("dataset_rspvar_schema.json")
    if param == "covariate":
        return await _load_json("dataset_covariate_schema.json")
    if param == "covariancematrix":
        # Use the analysis schema to derive this in the future
        return ["UN", "CS", "AR(1)", "TOEP"]
    return []


async def validate_param(param: str, value: Any) -> bool:
    """
    Simple validation: checks if value is within the allowed options list.
    """
    options = await list_options(param)
    if not options:
        return False
    if isinstance(options, list) and options and isinstance(options[0], dict):
        # dict list: match any value in any field
        for entry in options:
            if value in entry.values():
                return True
        return False
    return value in options
