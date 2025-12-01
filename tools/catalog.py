import json
from pathlib import Path
from typing import Any, Dict, List, Union

BASE = Path(__file__).resolve().parent.parent / "schema"


async def _load_json(name: str) -> List[Dict[str, Any]]:
    with open(BASE / name, "r") as f:
        return json.load(f)


async def list_options(param: str) -> Dict[str, Any]:
    """Return allowed options for a parameter from local schema catalogs.

    Args:
        param: Parameter name (endpoint, population, responsevariable, covariate, covariancematrix).

    Returns:
        dict: {"status": "success", "data": <list>} or {"status": "error", "error_message": "..."}.
    """
    param = param.lower()
    try:
        if param == "endpoint":
            data = await _load_json("dataset_endpoint_schema.json")
        elif param == "population":
            data = await _load_json("dataset_population_schema.json")
        elif param == "responsevariable":
            data = await _load_json("dataset_rspvar_schema.json")
        elif param == "covariate":
            data = await _load_json("dataset_covariate_schema.json")
        elif param == "covariancematrix":
            data = ["UN", "CS", "AR(1)", "TOEP"]
        else:
            return {"status": "error", "error_message": f"Unsupported parameter: {param}"}
        return {"status": "success", "data": data}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}


async def validate_param(param: str, value: Any) -> Dict[str, Union[str, bool]]:
    """Validate that a value is in the allowed options list.

    Args:
        param: Parameter name.
        value: Value to validate.

    Returns:
        dict: {"status": "success", "data": True/False} or {"status": "error", "error_message": "..."}.
    """
    options_resp = await list_options(param)
    if options_resp.get("status") != "success":
        return options_resp
    options = options_resp.get("data") or []
    is_valid = False
    if isinstance(options, list) and options and isinstance(options[0], dict):
        for entry in options:
            if value in entry.values():
                is_valid = True
                break
    else:
        is_valid = value in options
    return {"status": "success", "data": is_valid}
