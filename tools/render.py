async def render_markdown(text: str) -> dict:
    """Render markdown text (pass-through).

    Args:
        text: Markdown-compatible text.

    Returns:
        dict: {"status": "success", "data": text} or {"status": "error", "error_message": "..."}.
    """
    try:
        return {"status": "success", "data": text}
    except Exception as exc:
        return {"status": "error", "error_message": str(exc)}
