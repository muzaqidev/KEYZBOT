"""Task system — create, track, update tasks with dependencies."""

import json, time
from pathlib import Path

DIR = Path(__file__).parent.parent / "plans"
FILE = DIR / "tasks.json"

def _load():
    DIR.mkdir(parents=True, exist_ok=True)
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {"next_id": 1, "tasks": []}

def _save(data):
    DIR.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2))

def create(subject, description="", owner=""):
    data = _load()
    tid = str(data["next_id"])
    data["next_id"] += 1
    task = {
        "id": tid, "subject": subject, "description": description,
        "status": "pending", "owner": owner, "blocks": [], "blockedBy": [],
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["tasks"].append(task)
    _save(data)
    return task

def get(task_id):
    data = _load()
    for t in data["tasks"]:
        if t["id"] == str(task_id):
            return t
    return None

def list_all():
    data = _load()
    return data["tasks"]

def update(task_id, **kwargs):
    data = _load()
    for t in data["tasks"]:
        if t["id"] == str(task_id):
            for k, v in kwargs.items():
                if k in ("status", "subject", "description", "owner"):
                    t[k] = v
                elif k == "addBlocks":
                    for b in v:
                        if b not in t["blocks"]:
                            t["blocks"].append(b)
                elif k == "addBlockedBy":
                    for b in v:
                        if b not in t["blockedBy"]:
                            t["blockedBy"].append(b)
            _save(data)
            return t
    return None

def delete(task_id):
    data = _load()
    data["tasks"] = [t for t in data["tasks"] if t["id"] != str(task_id)]
    _save(data)

def get_output(task_id):
    """Check if task has a background output file."""
    out = Path("/tmp") / f"keyzbot-task-{task_id}.output"
    if out.exists():
        return out.read_text()
    return None
