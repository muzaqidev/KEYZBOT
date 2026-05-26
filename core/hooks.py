"""Hooks system — execute shell commands on events."""

import json, subprocess, os, shlex
from pathlib import Path

SETTINGS = Path.home() / ".openclaude" / "settings.json"

# ─── Hook Events ──────────────────────────────────────────────────────────────
# pre_tool_call, post_tool_call, pre_prompt, post_response

def load_hooks():
    """Load hooks from settings.json."""
    if not SETTINGS.exists():
        return {}
    try:
        with open(SETTINGS) as f:
            cfg = json.load(f)
        return cfg.get("hooks", {})
    except Exception:
        return {}

def run_hooks(event, context=None):
    """Run all hooks for a given event. Returns list of results."""
    hooks = load_hooks()
    event_hooks = hooks.get(event, [])
    if not event_hooks:
        return []

    results = []
    ctx = context or {}
    for hook in event_hooks:
        cmd = hook.get("command", "")
        if not cmd:
            continue
        # Substitute context vars (shell-escape values to prevent injection)
        for k, v in ctx.items():
            cmd = cmd.replace(f"{{{k}}}", shlex.quote(str(v)))
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=os.getcwd())
            results.append({
                "command": cmd,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
                "returncode": r.returncode,
            })
        except subprocess.TimeoutExpired:
            results.append({"command": cmd, "stdout": "", "stderr": "timeout", "returncode": -1})
        except Exception as e:
            results.append({"command": cmd, "stdout": "", "stderr": str(e), "returncode": -1})
    return results

def add_hook(event, command):
    """Add a hook to settings.json."""
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if SETTINGS.exists():
        try:
            cfg = json.loads(SETTINGS.read_text())
        except Exception:
            pass
    hooks = cfg.get("hooks", {})
    event_hooks = hooks.get(event, [])
    event_hooks.append({"command": command})
    hooks[event] = event_hooks
    cfg["hooks"] = hooks
    SETTINGS.write_text(json.dumps(cfg, indent=2))

def remove_hooks(event=None):
    """Remove hooks. If event given, only that event."""
    if not SETTINGS.exists():
        return
    cfg = json.loads(SETTINGS.read_text())
    if event:
        cfg.get("hooks", {}).pop(event, None)
    else:
        cfg.pop("hooks", None)
    SETTINGS.write_text(json.dumps(cfg, indent=2))
