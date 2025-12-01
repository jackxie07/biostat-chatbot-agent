from typing import Any, Dict, List


async def exit_loop(ask_for: List[str] | None = None) -> Dict[str, Any]:
    """
    Signal whether the parameter collection loop can exit based on ask_for.
    Returns {"loop_exit": True} when ask_for is empty/None, else False.
    """
    empty = not ask_for
    return {"loop_exit": empty}
