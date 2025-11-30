"""
SQLite-backed chat history to align with ADK's default lightweight storage.
"""

import os
import sqlite3
import json
from pathlib import Path

DB_PATH = os.getenv("ADK_DB_PATH", "adk.db")

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS chat_history (
        session_id INTEGER,
        chat_id INTEGER,
        role TEXT,
        content TEXT
    )
    """
)
conn.commit()


def _get_max(query, params=()):
    cursor.execute(query, params)
    res = cursor.fetchone()
    return res[0] if res and res[0] is not None else 0


def get_current_session():
    return _get_max("SELECT max(session_id) FROM chat_history")


def create_session():
    current_session = get_current_session()
    sys_content = "You are expert SAS programmer with lots of clinical trial domain and statistical analysis knowledge."
    cursor.execute(
        "INSERT INTO chat_history(session_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
        (current_session + 1, 1, "system", sys_content),
    )
    conn.commit()


def save_chat(role, content):
    current_session = get_current_session()
    new_chat = _get_max("SELECT max(chat_id) FROM chat_history WHERE session_id = ?", (current_session,)) + 1
    cursor.execute(
        "INSERT INTO chat_history(session_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
        (current_session, new_chat, role, content),
    )
    conn.commit()


