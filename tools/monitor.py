"""Monitor tool — run and monitor background processes."""

import subprocess, threading, time, os

# Track background processes
_processes = {}  # id -> {"proc": Popen, "output": [], "status": str, "started": str}
_next_id = 1

def start(command, work_dir=None):
    """Start a background process and return its ID."""
    global _next_id
    pid = str(_next_id)
    _next_id += 1

    try:
        proc = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=work_dir or os.getcwd(), text=True, bufsize=1
        )
        info = {
            "proc": proc, "output": [], "status": "running",
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "command": command, "id": pid,
        }
        _processes[pid] = info

        def _reader():
            for line in proc.stdout:
                info["output"].append(line.rstrip("\n"))
                if len(info["output"]) > 500:
                    info["output"] = info["output"][-500:]
            proc.wait()
            info["status"] = "completed" if proc.returncode == 0 else f"exit:{proc.returncode}"

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        return f"Process {pid} started: {command}"
    except Exception as e:
        return f"Error starting process: {e}"

def output(pid, tail=50):
    """Get output from a background process."""
    info = _processes.get(pid)
    if not info:
        return f"Process {pid} not found"
    lines = info["output"][-tail:]
    status = info["status"]
    return f"Process {pid} [{status}] ({len(info['output'])} lines):\n" + "\n".join(lines)

def status(pid=None):
    """Get status of background process(es)."""
    if pid:
        info = _processes.get(pid)
        if not info:
            return f"Process {pid} not found"
        return f"Process {pid}: {info['status']} | {info['command']} | {len(info['output'])} lines"
    if not _processes:
        return "No background processes"
    lines = []
    for pid, info in _processes.items():
        lines.append(f"[{pid}] {info['status']} | {info['command'][:60]} | {len(info['output'])} lines")
    return "\n".join(lines)

def stop(pid):
    """Stop a background process."""
    info = _processes.get(pid)
    if not info:
        return f"Process {pid} not found"
    try:
        info["proc"].terminate()
        info["status"] = "stopped"
        return f"Process {pid} stopped"
    except Exception as e:
        return f"Error stopping process {pid}: {e}"

# Tool definitions
TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "monitor_start",
            "description": "Start a background process and monitor its output. Use for long-running commands (servers, builds, watchers).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run in background"},
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "monitor_output",
            "description": "Get output from a running background process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_id": {"type": "string", "description": "Process ID"},
                    "tail": {"type": "integer", "description": "Number of last lines (default 50)"}
                },
                "required": ["process_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "monitor_status",
            "description": "Check status of background processes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_id": {"type": "string", "description": "Process ID (empty for all)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "monitor_stop",
            "description": "Stop a running background process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_id": {"type": "string", "description": "Process ID to stop"}
                },
                "required": ["process_id"]
            }
        }
    },
]

TOOL_NAMES = {"monitor_start", "monitor_output", "monitor_status", "monitor_stop"}

def execute(name, args, work_dir=None):
    if name == "monitor_start":
        return start(args.get("command", ""), work_dir)
    elif name == "monitor_output":
        return output(args.get("process_id", ""), args.get("tail", 50))
    elif name == "monitor_status":
        return status(args.get("process_id"))
    elif name == "monitor_stop":
        return stop(args.get("process_id", ""))
    return f"Unknown monitor tool: {name}"
