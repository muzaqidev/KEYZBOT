"""Permission system — auto-approve/deny per tool, user confirmation."""

import json
from pathlib import Path

SETTINGS = Path(__file__).parent.parent / "settings.json"

# Default permission modes
_MODES = {
    "auto": "Auto-approve all tool calls",
    "confirm": "Ask user before each tool call",
    "smart": "Auto-approve safe tools, confirm destructive ones",
}

# Tool safety classification
_SAFE_TOOLS = {"read_file", "glob_files", "grep_files", "list_dir", "web_search", "web_fetch"}
_DESTRUCTIVE_TOOLS = {"write_file", "edit_file", "bash"}

# Per-session state (keyed by session_id)
_sessions = {}  # session_id -> {"mode": str, "overrides": dict}
_default_mode = "smart"
_sandbox_mode = "off"  # off, warn, block

def _get_session(sid="default"):
    """Get or create session state."""
    if sid not in _sessions:
        _sessions[sid] = {"mode": _default_mode, "overrides": {}}
    return _sessions[sid]

def set_mode(mode, sid="default"):
    if mode in _MODES:
        _get_session(sid)["mode"] = mode
        return True
    return False

def get_mode(sid="default"):
    return _get_session(sid)["mode"]

def get_modes():
    return _MODES

def check(tool_name, args=None, sid="default"):
    """Check if a tool call should be allowed.
    Returns: ("approve", reason) or ("confirm", reason) or ("deny", reason)
    """
    session = _get_session(sid)

    # Check session overrides first
    if tool_name in session["overrides"]:
        action = session["overrides"][tool_name]
        return (action, f"Session override: {action}")

    # Check settings.json for persistent rules
    persistent = _load_persistent()
    if tool_name in persistent:
        return (persistent[tool_name], f"Settings rule: {persistent[tool_name]}")

    # Apply mode logic
    mode = session["mode"]
    if mode == "auto":
        return ("approve", "Auto mode")
    elif mode == "confirm":
        return ("confirm", "Confirm mode")
    elif mode == "smart":
        if tool_name in _SAFE_TOOLS:
            return ("approve", "Safe tool")
        elif tool_name in _DESTRUCTIVE_TOOLS:
            # Check bash for dangerous commands
            if tool_name == "bash" and args:
                cmd = args.get("command", "")
                if _is_dangerous(cmd):
                    return ("confirm", "Destructive bash command")
            return ("confirm", "Destructive tool — needs confirmation")

    return ("approve", "Default")

def _is_dangerous(cmd):
    """Check if a bash command is potentially dangerous."""
    dangerous = ["rm -rf", "rm -r /", "mkfs", "dd if=", "> /dev/", "chmod 777",
                 "git push --force", "git reset --hard", "DROP TABLE", "DELETE FROM",
                 "shutdown", "reboot", "kill -9", "pkill"]
    cmd_lower = cmd.lower()
    for pattern in dangerous:
        if pattern.lower() in cmd_lower:
            return True
    return False

def override(tool_name, action, sid="default"):
    """Set session override for a tool: 'approve' or 'deny'."""
    _get_session(sid)["overrides"][tool_name] = action

def clear_overrides(sid="default"):
    _get_session(sid)["overrides"].clear()

def cleanup_session(sid):
    """Remove session state."""
    _sessions.pop(sid, None)

def _load_persistent():
    """Load persistent permission rules from settings.json."""
    if not SETTINGS.exists():
        return {}
    try:
        cfg = json.loads(SETTINGS.read_text())
        return cfg.get("permissions", {}).get("tools", {})
    except Exception:
        return {}

def save_persistent(tool_name, action):
    """Save a persistent permission rule."""
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if SETTINGS.exists():
        try:
            cfg = json.loads(SETTINGS.read_text())
        except Exception:
            pass
    perms = cfg.get("permissions", {})
    tools = perms.get("tools", {})
    tools[tool_name] = action
    perms["tools"] = tools
    cfg["permissions"] = perms
    SETTINGS.write_text(json.dumps(cfg, indent=2))


def set_sandbox_mode(mode):
    """Set sandbox mode: off, warn, block."""
    global _sandbox_mode
    if mode in ("off", "warn", "block"):
        _sandbox_mode = mode
        return True
    return False


def get_sandbox_mode():
    """Get current sandbox mode."""
    return _sandbox_mode
