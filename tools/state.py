from typing import Any, Dict, List, Optional


async def exit_loop(ask_for: Optional[List[str]] = None) -> Dict[str, Any]:
    """Signal whether the parameter collection loop can exit based on ask_for.

    Args:
        ask_for: List of remaining parameters to collect.

    Returns:
        dict: {"status": "success", "data": {"loop_exit": bool}}.
    """
    empty = not ask_for
    return {"status": "success", "data": {"loop_exit": empty}}
