from typing import Any, Dict

import SASConnect


async def run_sas(analysis_detail: Dict[str, Any]) -> str:
    """
    Execute SAS analysis using existing SASConnect helper. Returns the output URL.
    """
    return SASConnect.execute_analysis(analysis_detail)
