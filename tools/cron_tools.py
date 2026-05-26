"""Cron/scheduler tools — create and manage scheduled tasks."""

import json, time
from pathlib import Path

FILE = Path(__file__).parent.parent / "plans" / "scheduled.json"

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "cron_create",
            "description": "Schedule a recurring or one-shot task. Uses 5-field cron: min hour dom month dow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cron": {"type": "string", "description": "Cron expression (5-field: min hour dom month dow)"},
                    "prompt": {"type": "string", "description": "The prompt/task to execute at each trigger"},
                    "recurring": {"type": "boolean", "description": "true = recurring, false = one-shot (default true)"}
                },
                "required": ["cron", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cron_list",
            "description": "List all scheduled jobs.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cron_delete",
            "description": "Delete a scheduled job by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "Job ID to delete"}
                },
                "required": ["job_id"]
            }
        }
    }
]

TOOL_NAMES = {"cron_create", "cron_list", "cron_delete"}

def _load():
    FILE.parent.mkdir(parents=True, exist_ok=True)
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {"next_id": 1, "jobs": []}

def _save(data):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2))

def execute(name, args, work_dir=None):
    if name == "cron_create":
        data = _load()
        jid = str(data["next_id"])
        data["next_id"] += 1
        job = {
            "id": jid, "cron": args.get("cron", ""),
            "prompt": args.get("prompt", ""),
            "recurring": args.get("recurring", True),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "active": True,
        }
        data["jobs"].append(job)
        _save(data)
        return f"Job #{jid} scheduled: {job['cron']} -> {job['prompt'][:60]}"

    elif name == "cron_list":
        data = _load()
        if not data["jobs"]:
            return "No scheduled jobs"
        lines = []
        for j in data["jobs"]:
            status = "active" if j.get("active") else "paused"
            recurring = "recurring" if j.get("recurring") else "one-shot"
            lines.append(f"#{j['id']} [{status}/{recurring}] {j['cron']} -> {j.get('prompt', '')[:60]}")
        return "\n".join(lines)

    elif name == "cron_delete":
        jid = args.get("job_id", "")
        data = _load()
        original_len = len(data["jobs"])
        data["jobs"] = [j for j in data["jobs"] if j["id"] != str(jid)]
        if len(data["jobs"]) < original_len:
            _save(data)
            return f"Job #{jid} deleted"
        return f"Job #{jid} not found"

    return f"Unknown tool: {name}"
