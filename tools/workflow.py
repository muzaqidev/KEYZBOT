"""Workflow automation tools — pipelines, watchers, logging."""

import subprocess, os, json, time, hashlib

TOOL_DEFS = [
    {"type": "function", "function": {"name": "pipeline", "description": "Chain multiple shell commands in sequence. Stops on first failure.", "parameters": {"type": "object", "properties": {"commands": {"type": "array", "items": {"type": "string"}, "description": "Commands to run in sequence"}, "stop_on_error": {"type": "boolean", "description": "Stop on first failure (default true)"}}, "required": ["commands"]}}},
    {"type": "function", "function": {"name": "watch_file", "description": "Watch a file for changes and return when modified.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File to watch"}, "timeout": {"type": "integer", "description": "Max wait in seconds (default 60)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "retry", "description": "Retry a command with exponential backoff on failure.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Command to retry"}, "max_retries": {"type": "integer", "description": "Max retry attempts (default 3)"}, "delay": {"type": "integer", "description": "Initial delay in seconds (default 2)"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "log_write", "description": "Write a timestamped entry to a log file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Log file path"}, "message": {"type": "string", "description": "Log message"}, "level": {"type": "string", "enum": ["INFO", "WARN", "ERROR", "DEBUG"], "description": "Log level (default INFO)"}}, "required": ["path", "message"]}}},
    {"type": "function", "function": {"name": "log_read", "description": "Read log file entries with optional filtering.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Log file path"}, "tail": {"type": "integer", "description": "Last N lines (default 50)"}, "level": {"type": "string", "description": "Filter by level"}, "search": {"type": "string", "description": "Filter by text"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "env_file_load", "description": "Load environment variables from a .env file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to .env file"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "env_file_save", "description": "Save current env vars to a .env file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Output .env file path"}, "vars": {"type": "array", "items": {"type": "string"}, "description": "Variable names to save (omit for all)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "config_read", "description": "Read a config file (INI, TOML, JSON, YAML).", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Config file path"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "config_write", "description": "Write/update a config file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Config file path"}, "data": {"type": "string", "description": "Config data as JSON"}, "format": {"type": "string", "enum": ["json", "ini", "yaml"], "description": "File format (auto-detected from extension)"}}, "required": ["path", "data"]}}},
    {"type": "function", "function": {"name": "schedule_cron", "description": "Add a system crontab entry.", "parameters": {"type": "object", "properties": {"expression": {"type": "string", "description": "Cron expression (5-field)"}, "command": {"type": "string", "description": "Command to run"}, "comment": {"type": "string", "description": "Comment for the entry"}}, "required": ["expression", "command"]}}},
    {"type": "function", "function": {"name": "rate_limit", "description": "Wait/pause execution for a specified duration.", "parameters": {"type": "object", "properties": {"seconds": {"type": "number", "description": "Seconds to wait"}}, "required": ["seconds"]}}},
    {"type": "function", "function": {"name": "checksum_verify", "description": "Verify file integrity by comparing checksums.", "parameters": {"type": "object", "properties": {"file": {"type": "string", "description": "File path"}, "expected": {"type": "string", "description": "Expected hash"}, "algorithm": {"type": "string", "enum": ["md5", "sha1", "sha256"], "description": "Hash algorithm (default sha256)"}}, "required": ["file", "expected"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "pipeline":
            commands = args["commands"]
            stop_on_error = args.get("stop_on_error", True)
            results = []
            for i, cmd in enumerate(commands):
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=work_dir)
                status = "OK" if r.returncode == 0 else f"FAIL (exit {r.returncode})"
                output = r.stdout.strip() or r.stderr.strip() or "(no output)"
                results.append(f"[{i+1}/{len(commands)}] {cmd}\n  {status}: {output[:200]}")
                if r.returncode != 0 and stop_on_error:
                    results.append(f"Pipeline stopped at step {i+1}")
                    break
            return "\n".join(results)

        elif name == "watch_file":
            path = args["path"]
            timeout = args.get("timeout", 60)
            if not os.path.exists(path):
                return f"Error: File not found: {path}"
            initial_mtime = os.path.getmtime(path)
            start = time.time()
            while time.time() - start < timeout:
                time.sleep(1)
                if os.path.getmtime(path) != initial_mtime:
                    return f"File changed: {path}"
            return f"No changes detected in {timeout}s"

        elif name == "retry":
            cmd = args["command"]
            max_retries = args.get("max_retries", 3)
            delay = args.get("delay", 2)
            for attempt in range(max_retries + 1):
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=work_dir)
                if r.returncode == 0:
                    return f"Success (attempt {attempt + 1}):\n{r.stdout[:2000]}"
                if attempt < max_retries:
                    time.sleep(delay * (2 ** attempt))
            return f"Failed after {max_retries + 1} attempts:\n{r.stderr[:2000]}"

        elif name == "log_write":
            path = args["path"]
            level = args.get("level", "INFO")
            message = args["message"]
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            line = f"[{ts}] [{level}] {message}\n"
            with open(path, "a") as f:
                f.write(line)
            return f"Logged to {path}"

        elif name == "log_read":
            path = args["path"]
            if not os.path.exists(path):
                return f"Log file not found: {path}"
            with open(path) as f:
                lines = f.readlines()
            if args.get("level"):
                lines = [l for l in lines if f"[{args['level']}]" in l]
            if args.get("search"):
                lines = [l for l in lines if args["search"].lower() in l.lower()]
            tail = args.get("tail", 50)
            return "".join(lines[-tail:]) or "(no matching entries)"

        elif name == "env_file_load":
            path = args["path"]
            loaded = 0
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
                        loaded += 1
            return f"Loaded {loaded} variables from {path}"

        elif name == "env_file_save":
            path = args["path"]
            vars_to_save = args.get("vars")
            with open(path, "w") as f:
                if vars_to_save:
                    for v in vars_to_save:
                        f.write(f"{v}={os.environ.get(v, '')}\n")
                else:
                    for k, v in sorted(os.environ.items()):
                        f.write(f"{k}={v}\n")
            return f"Saved to {path}"

        elif name == "config_read":
            path = args["path"]
            if path.endswith(".json"):
                with open(path) as f:
                    return json.dumps(json.load(f), indent=2)[:5000]
            elif path.endswith((".yaml", ".yml")):
                import yaml
                with open(path) as f:
                    return json.dumps(yaml.safe_load(f), indent=2)[:5000]
            elif path.endswith(".ini"):
                import configparser
                c = configparser.ConfigParser()
                c.read(path)
                data = {s: dict(c.items(s)) for s in c.sections()}
                return json.dumps(data, indent=2)[:5000]
            elif path.endswith(".toml"):
                import tomllib
                with open(path, "rb") as f:
                    return json.dumps(tomllib.load(f), indent=2)[:5000]
            with open(path) as f:
                return f.read()[:5000]

        elif name == "config_write":
            path = args["path"]
            data = json.loads(args["data"])
            fmt = args.get("format", "")
            if not fmt:
                if path.endswith(".json"): fmt = "json"
                elif path.endswith((".yaml", ".yml")): fmt = "yaml"
                elif path.endswith(".ini"): fmt = "ini"
                else: fmt = "json"
            if fmt == "json":
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
            elif fmt == "yaml":
                import yaml
                with open(path, "w") as f:
                    yaml.dump(data, f, default_flow_style=False)
            elif fmt == "ini":
                import configparser
                c = configparser.ConfigParser()
                for section, values in data.items():
                    c[section] = values
                with open(path, "w") as c:
                    c.write(str(data))
            return f"Written to {path}"

        elif name == "schedule_cron":
            expr = args["expression"]
            cmd = args["command"]
            comment = args.get("comment", "keyzbot")
            cron_line = f"{expr} {cmd} # {comment}"
            r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
            existing = r.stdout if r.returncode == 0 else ""
            new_cron = existing.rstrip() + "\n" + cron_line + "\n"
            proc = subprocess.run(["crontab", "-"], input=new_cron, capture_output=True, text=True, timeout=5)
            return f"Added crontab entry: {cron_line}" if proc.returncode == 0 else f"Error: {proc.stderr}"

        elif name == "rate_limit":
            secs = float(args["seconds"])
            time.sleep(min(secs, 300))
            return f"Waited {secs}s"

        elif name == "checksum_verify":
            algo = args.get("algorithm", "sha256")
            h = hashlib.new(algo)
            with open(args["file"], "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            actual = h.hexdigest()
            match = actual == args["expected"].lower()
            return f"Algorithm: {algo}\nExpected: {args['expected']}\nActual: {actual}\nMatch: {'YES' if match else 'NO'}"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
