"""Persistent storage for web chat sessions."""

import json, os, time
from pathlib import Path

_DIR = Path(__file__).parent.parent
_STORE_FILE = _DIR / "history" / "web_sessions.json"


def _load_raw():
    """Load raw session data from disk."""
    if _STORE_FILE.exists():
        try:
            with open(_STORE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"sessions": {}, "version": 1}


def _save_raw(data):
    """Save raw session data to disk."""
    _STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_STORE_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_sessions():
    """Load all persisted sessions. Returns dict of browser_sid -> session data."""
    raw = _load_raw()
    return raw.get("sessions", {})


def save_session(browser_sid, session_data):
    """Save a single session to disk.

    session_data should contain:
    - chats: dict of chat_id -> {id, name, messages, work_dir, created, messages_count}
    - active_chat: str
    """
    data = _load_raw()
    # Serialize chat messages (strip agent objects, keep messages)
    serialized_chats = {}
    for cid, chat in session_data.get("chats", {}).items():
        agent = chat.get("agent")
        messages = agent.messages if agent else chat.get("messages", [])
        serialized_chats[cid] = {
            "id": chat.get("id", cid),
            "name": chat.get("name", "New Chat"),
            "messages": messages,
            "work_dir": chat.get("work_dir", ""),
            "created": chat.get("created", ""),
            "messages_count": chat.get("messages_count", 0),
        }
    data["sessions"][browser_sid] = {
        "chats": serialized_chats,
        "active_chat": session_data.get("active_chat", ""),
        "last_active": time.time(),
    }
    _save_raw(data)


def save_all_sessions(sessions_dict):
    """Save all sessions at once (for periodic sync).

    sessions_dict: {browser_sid: session_data_with_agents}
    """
    data = _load_raw()
    for browser_sid, session_data in sessions_dict.items():
        serialized_chats = {}
        for cid, chat in session_data.get("chats", {}).items():
            agent = chat.get("agent")
            messages = agent.messages if agent else chat.get("messages", [])
            serialized_chats[cid] = {
                "id": chat.get("id", cid),
                "name": chat.get("name", "New Chat"),
                "messages": messages,
                "work_dir": chat.get("work_dir", ""),
                "created": chat.get("created", ""),
                "messages_count": chat.get("messages_count", 0),
            }
        data["sessions"][browser_sid] = {
            "chats": serialized_chats,
            "active_chat": session_data.get("active_chat", ""),
            "last_active": time.time(),
        }
    _save_raw(data)


def delete_session(browser_sid):
    """Remove a session from disk."""
    data = _load_raw()
    data["sessions"].pop(browser_sid, None)
    _save_raw(data)


def delete_chat(browser_sid, chat_id):
    """Remove a single chat from a session."""
    data = _load_raw()
    session = data["sessions"].get(browser_sid)
    if session:
        session["chats"].pop(chat_id, None)
        if not session["chats"]:
            del data["sessions"][browser_sid]
        _save_raw(data)


def get_restored_chats(browser_sid):
    """Get restored chats for a browser session (messages only, no agent)."""
    data = _load_raw()
    session = data["sessions"].get(browser_sid, {})
    return session.get("chats", {}), session.get("active_chat", "")
