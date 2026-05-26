"""Plan mode — explore and design before implementation."""

import os, time, json
from pathlib import Path

DIR = Path(__file__).parent.parent / "plans"

# ─── State ────────────────────────────────────────────────────────────────────
_active_plan = None  # Current plan file path

# ─── Plan Operations ─────────────────────────────────────────────────────────
def enter(title, description=""):
    """Enter plan mode, create a plan file."""
    global _active_plan
    DIR.mkdir(parents=True, exist_ok=True)
    safe = title.lower().replace(" ", "-")[:40]
    safe = "".join(c for c in safe if c.isalnum() or c == '-')
    fname = f"{safe}-{int(time.time())}.md"
    fpath = DIR / fname

    content = f"""# Plan: {title}

{description}

## Status: DRAFT

## Exploration Notes
(Use this section to document what you learn while exploring the codebase)

## Implementation Steps
1. (to be filled)

## Critical Files
(list files that will be changed)

## Questions / Concerns
(any open questions for the user)
"""
    fpath.write_text(content)
    _active_plan = str(fpath)
    return _active_plan

def get_active():
    """Get the currently active plan path."""
    return _active_plan

def exit_plan():
    """Exit plan mode (keep file)."""
    global _active_plan
    path = _active_plan
    _active_plan = None
    return path

def update(content):
    """Update the active plan content."""
    global _active_plan
    if not _active_plan:
        return None
    Path(_active_plan).write_text(content)
    return _active_plan

def read():
    """Read the active plan content."""
    global _active_plan
    if not _active_plan:
        return None
    return Path(_active_plan).read_text()

def list_plans():
    """List all saved plans."""
    DIR.mkdir(parents=True, exist_ok=True)
    plans = []
    for f in sorted(DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
        text = f.read_text()
        title = ""
        status = "DRAFT"
        for line in text.split("\n"):
            if line.startswith("# Plan:"):
                title = line[7:].strip()
            if "## Status:" in line:
                status = line.replace("## Status:", "").strip()
        plans.append({
            "file": str(f),
            "title": title or f.stem,
            "status": status,
        })
    return plans

def mark_status(status):
    """Update plan status (DRAFT, IN_PROGRESS, COMPLETE)."""
    global _active_plan
    if not _active_plan:
        return None
    text = Path(_active_plan).read_text()
    text = text.replace("## Status: DRAFT", f"## Status: {status}")
    text = text.replace("## Status: IN_PROGRESS", f"## Status: {status}")
    text = text.replace("## Status: COMPLETE", f"## Status: {status}")
    Path(_active_plan).write_text(text)
    return status
