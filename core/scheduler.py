"""Scheduler — cron-like recurring and one-shot tasks."""

import json, time
from pathlib import Path

FILE = Path(__file__).parent.parent / "plans" / "scheduled.json"
_jobs = {}  # id -> threading.Timer

def _load():
    FILE.parent.mkdir(parents=True, exist_ok=True)
    if FILE.exists():
        return json.loads(FILE.read_text())
    return {"next_id": 1, "jobs": []}

def _save(data):
    FILE.write_text(json.dumps(data, indent=2))

def create(cron_expr, prompt, durable=False, recurring=True):
    """Create a scheduled job. Returns job ID."""
    data = _load()
    jid = str(data["next_id"])
    data["next_id"] += 1
    job = {
        "id": jid, "cron": cron_expr, "prompt": prompt,
        "durable": durable, "recurring": recurring,
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active": True,
    }
    data["jobs"].append(job)
    _save(data)
    return job

def list_jobs():
    data = _load()
    return data["jobs"]

def delete(jid):
    data = _load()
    data["jobs"] = [j for j in data["jobs"] if j["id"] != str(jid)]
    _save(data)
    # Cancel timer if running
    t = _jobs.pop(jid, None)
    if t:
        t.cancel()

def get(jid):
    data = _load()
    for j in data["jobs"]:
        if j["id"] == str(jid):
            return j
    return None

def parse_cron(expr):
    """Parse a 5-field cron expression: min hour dom month dow.
    Returns (minute, hour, dom, month, dow) as strings."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return None
    return tuple(parts)

def should_fire(cron_expr, now=None):
    """Check if a cron expression matches current time."""
    if now is None:
        now = time.localtime()
    parsed = parse_cron(cron_expr)
    if not parsed:
        return False
    cm, ch, cdom, cmon, cdow = parsed
    checks = [
        (cm, now.tm_min), (ch, now.tm_hour),
        (cdom, now.tm_mday), (cmon, now.tm_mon), (cdow, now.tm_wday),
    ]
    for pattern, val in checks:
        if pattern == "*":
            continue
        if "/" in pattern:
            base, step = pattern.split("/")
            if base == "*":
                if val % int(step) != 0:
                    return False
                continue
        if "," in pattern:
            if val not in [int(x) for x in pattern.split(",")]:
                return False
            continue
        if "-" in pattern:
            lo, hi = pattern.split("-")
            if not (int(lo) <= val <= int(hi)):
                return False
            continue
        if int(pattern) != val:
            return False
    return True
