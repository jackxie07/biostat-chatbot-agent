import json
from pathlib import Path
from typing import Any, Dict

LOG_DIR = Path("chat_history")
LOG_DIR.mkdir(parents=True, exist_ok=True)


async def persist_session(state: Dict[str, Any]) -> str:
    """
    Persist session state to a rolling JSON log. Returns path to the log file.
    """
    session_id = state.get("session_id", "unknown")
    path = LOG_DIR / f"session_{session_id}.jsonl"
    with path.open("a") as f:
        f.write(json.dumps(state) + "\n")
    return str(path)
