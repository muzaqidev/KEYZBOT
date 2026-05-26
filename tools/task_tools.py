"""Task management tools — create, track, update tasks with dependencies."""

import json, time
from pathlib import Path

DIR = Path(__file__).parent.parent / "plans"
FILE = DIR / "tasks.json"

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Create a new task to track work. Use for complex multi-step tasks that need progress tracking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Brief task title (imperative form)"},
                    "description": {"type": "string", "description": "Detailed task description"}
                },
                "required": ["subject"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_update",
            "description": "Update a task's status, subject, or description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to update"},
                    "status": {"type": "string", "description": "New status: pending, in_progress, completed, deleted"},
                    "subject": {"type": "string", "description": "New task title"},
                    "description": {"type": "string", "description": "New task description"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_list",
            "description": "List all tasks, optionally filtered by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: pending, in_progress, completed (omit for all)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_delete",
            "description": "Permanently delete a task from storage. This cannot be undone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID to permanently delete"}
                },
                "required": ["task_id"]
            }
        }
    }
]

TOOL_NAMES = {"task_create", "task_update", "task_list", "task_delete"}

def _load():
    DIR.mkdir(parents=True, exist_ok=True)
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {"next_id": 1, "tasks": []}

def _save(data):
    DIR.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2))

def execute(name, args, work_dir=None):
    if name == "task_create":
        data = _load()
        tid = str(data["next_id"])
        data["next_id"] += 1
        task = {
            "id": tid, "subject": args.get("subject", ""),
            "description": args.get("description", ""),
            "status": "pending", "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["tasks"].append(task)
        _save(data)
        return f"Task #{tid} created: {task['subject']}"

    elif name == "task_update":
        tid = args.get("task_id", "")
        data = _load()
        for t in data["tasks"]:
            if t["id"] == str(tid):
                if "status" in args:
                    t["status"] = args["status"]
                if "subject" in args:
                    t["subject"] = args["subject"]
                if "description" in args:
                    t["description"] = args["description"]
                _save(data)
                return f"Task #{tid} updated: {t['subject']} [{t['status']}]"
        return f"Task #{tid} not found"

    elif name == "task_list":
        data = _load()
        status_filter = args.get("status", "")
        tasks = data["tasks"]
        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]
        if not tasks:
            return "No tasks found"
        lines = []
        for t in tasks:
            lines.append(f"#{t['id']} [{t['status']}] {t['subject']}")
        return "\n".join(lines)

    elif name == "task_delete":
        tid = args.get("task_id", "")
        data = _load()
        found = False
        for t in data["tasks"]:
            if t["id"] == str(tid):
                found = True
                subject = t["subject"]
                break
        if not found:
            return f"Task #{tid} not found"
        data["tasks"] = [t for t in data["tasks"] if t["id"] != str(tid)]
        _save(data)
        return f"Task #{tid} permanently deleted: {subject}"

    return f"Unknown tool: {name}"
