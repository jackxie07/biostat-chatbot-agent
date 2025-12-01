import json
from pathlib import Path
from typing import Any, Dict

LOG_DIR = Path("chat_history")
LOG_DIR.mkdir(parents=True, exist_ok=True)


async def persist_session(state: Dict[str, Any]) -> Dict[str, Any]:
    """Persist session state to a rolling JSON log.

    Args:
        state: Session state dict to persist.

    Returns:
        dict: {"status": "success", "data": <path>} or {"status": "error", "error_message": "..."}.
    """
    try:
        session_id = state.get("session_id", "unknown")
        path = LOG_DIR / f"session_{session_id}.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(state) + "\n")
        return {"status": "success", "data": str(path)}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}
