from typing import Any, Dict

import SASConnect


async def run_sas(analysis_detail: Dict[str, Any]) -> Dict[str, Any]:
    """Execute SAS analysis using SASConnect helper.

    Args:
        analysis_detail: Analysis configuration collected from the workflow.

    Returns:
        dict: {"status": "success", "data": <url>} or {"status": "error", "error_message": "..."}.
    """
    try:
        url = SASConnect.execute_analysis(analysis_detail)
        return {"status": "success", "data": url}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}
