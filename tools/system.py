"""System information and process management tools."""

import subprocess, os, platform, json, signal

TOOL_DEFS = [
    {"type": "function", "function": {"name": "sys_info", "description": "Get system information: OS, CPU, memory, disk, Python version.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "cpu_info", "description": "Get CPU details: cores, model, usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "memory_info", "description": "Get memory usage details (total, used, free, swap).", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "disk_info", "description": "Get disk usage for all mounted filesystems.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Specific path to check (default: all)"}}, "required": []}}},
    {"type": "function", "function": {"name": "process_list", "description": "List running processes with PID, name, CPU, and memory usage.", "parameters": {"type": "object", "properties": {"filter": {"type": "string", "description": "Filter by process name"}, "sort_by": {"type": "string", "enum": ["cpu", "memory", "pid", "name"], "description": "Sort by (default memory)"}}, "required": []}}},
    {"type": "function", "function": {"name": "process_info", "description": "Get detailed info about a process by PID.", "parameters": {"type": "object", "properties": {"pid": {"type": "integer", "description": "Process ID"}}, "required": ["pid"]}}},
    {"type": "function", "function": {"name": "process_kill", "description": "Kill a process by PID or name.", "parameters": {"type": "object", "properties": {"pid": {"type": "integer", "description": "Process ID"}, "name": {"type": "string", "description": "Process name (kills all matching)"}, "signal": {"type": "string", "enum": ["TERM", "KILL", "HUP", "INT"], "description": "Signal to send (default TERM)"}}, "required": []}}},
    {"type": "function", "function": {"name": "env_list", "description": "List all environment variables.", "parameters": {"type": "object", "properties": {"filter": {"type": "string", "description": "Filter by name pattern"}}, "required": []}}},
    {"type": "function", "function": {"name": "env_get", "description": "Get an environment variable value.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Variable name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "env_set", "description": "Set an environment variable for the current session.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Variable name"}, "value": {"type": "string", "description": "Value to set"}}, "required": ["name", "value"]}}},
    {"type": "function", "function": {"name": "uptime", "description": "Get system uptime and load averages.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "whoami", "description": "Get current user info: username, UID, groups, home directory.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "hostname_info", "description": "Get hostname and network identity.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "os_version", "description": "Get detailed OS version and distribution info.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "temp_dir", "description": "Get system temp directory and its usage.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "shell_info", "description": "Get current shell info: type, version, PATH.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "python_info", "description": "Get Python environment details: version, packages, site-packages path.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "sys_info":
            import shutil
            uname = platform.uname()
            disk = shutil.disk_usage("/")
            mem = ""
            try:
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                    total = int(lines[0].split()[1]) // 1024
                    avail = int(lines[2].split()[1]) // 1024
                    mem = f"Memory: {total}MB total, {avail}MB available"
            except:
                mem = "Memory: N/A"
            return "\n".join([
                f"OS: {uname.system} {uname.release}",
                f"Node: {uname.node}",
                f"Machine: {uname.machine}",
                f"Processor: {uname.processor}",
                mem,
                f"Disk: {disk.total // (1024**3)}GB total, {disk.free // (1024**3)}GB free",
                f"Python: {platform.python_version()}",
            ])

        elif name == "cpu_info":
            lines = []
            try:
                with open("/proc/cpuinfo") as f:
                    content = f.read()
                model = [l for l in content.split("\n") if "model name" in l]
                cores = [l for l in content.split("\n") if "processor" in l]
                if model:
                    lines.append(f"Model: {model[0].split(':')[1].strip()}")
                lines.append(f"Cores: {len(cores)}")
            except:
                lines.append(f"Cores: {os.cpu_count()}")
                lines.append(f"Architecture: {platform.machine()}")
            try:
                r = subprocess.run(["top", "-bn1"], capture_output=True, text=True, timeout=5)
                for line in r.stdout.split("\n"):
                    if "Cpu" in line or "cpu" in line:
                        lines.append(f"Usage: {line.strip()}")
                        break
            except:
                pass
            return "\n".join(lines)

        elif name == "memory_info":
            try:
                with open("/proc/meminfo") as f:
                    info = {}
                    for line in f.readlines()[:20]:
                        parts = line.split()
                        info[parts[0].rstrip(":")] = int(parts[1])
                total = info.get("MemTotal", 0) // 1024
                free = info.get("MemFree", 0) // 1024
                available = info.get("MemAvailable", 0) // 1024
                buffers = info.get("Buffers", 0) // 1024
                cached = info.get("Cached", 0) // 1024
                swap_total = info.get("SwapTotal", 0) // 1024
                swap_free = info.get("SwapFree", 0) // 1024
                used = total - available
                return "\n".join([
                    f"Total: {total}MB",
                    f"Used: {used}MB ({used * 100 // total}%)" if total else "Used: N/A",
                    f"Available: {available}MB",
                    f"Buffers: {buffers}MB",
                    f"Cached: {cached}MB",
                    f"Swap: {swap_total - swap_free}MB / {swap_total}MB",
                ])
            except:
                return "Memory info not available"

        elif name == "disk_info":
            import shutil
            path = args.get("path", "/")
            try:
                usage = shutil.disk_usage(path)
                return f"Path: {path}\nTotal: {usage.total // (1024**3)}GB\nUsed: {usage.used // (1024**3)}GB\nFree: {usage.free // (1024**3)}GB\nUsage: {usage.used * 100 // usage.total}%"
            except:
                r = subprocess.run(["df", "-h"], capture_output=True, text=True, timeout=5)
                return r.stdout[:3000]

        elif name == "process_list":
            sort_by = args.get("sort_by", "memory")
            filt = args.get("filter", "")
            sort_flag = {"cpu": "-%cpu", "memory": "-%mem", "pid": "pid", "name": "comm"}.get(sort_by, "-%mem")
            cmd = ["ps", "aux", "--sort", sort_flag]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = r.stdout.strip().split("\n")
            if filt:
                lines = [lines[0]] + [l for l in lines[1:] if filt.lower() in l.lower()]
            return "\n".join(lines[:60])

        elif name == "process_info":
            pid = args["pid"]
            try:
                with open(f"/proc/{pid}/status") as f:
                    status = f.read()
                with open(f"/proc/{pid}/cmdline") as f:
                    cmdline = f.read().replace("\x00", " ").strip()
                return f"PID: {pid}\n\n{status}\nCommand: {cmdline}"
            except FileNotFoundError:
                return f"Process {pid} not found"

        elif name == "process_kill":
            sig = {"TERM": signal.SIGTERM, "KILL": signal.SIGKILL, "HUP": signal.SIGHUP, "INT": signal.SIGINT}.get(args.get("signal", "TERM"), signal.SIGTERM)
            if args.get("pid"):
                os.kill(args["pid"], sig)
                return f"Sent {args.get('signal', 'TERM')} to PID {args['pid']}"
            elif args.get("name"):
                r = subprocess.run(["pkill", f"-{args.get('signal', 'TERM')}", args["name"]], capture_output=True, text=True, timeout=5)
                return r.stdout or f"Sent signal to processes matching '{args['name']}'"
            return "Error: specify pid or name"

        elif name == "env_list":
            filt = args.get("filter", "")
            envs = os.environ
            if filt:
                envs = {k: v for k, v in envs.items() if filt.upper() in k.upper()}
            lines = [f"{k}={v}" for k, v in sorted(envs.items())]
            return "\n".join(lines[:100]) or "(no matching env vars)"

        elif name == "env_get":
            return os.environ.get(args["name"], f"'{args['name']}' not set")

        elif name == "env_set":
            os.environ[args["name"]] = args["value"]
            return f"Set {args['name']}={args['value']}"

        elif name == "uptime":
            try:
                with open("/proc/uptime") as f:
                    uptime_secs = float(f.read().split()[0])
                days = int(uptime_secs // 86400)
                hours = int((uptime_secs % 86400) // 3600)
                mins = int((uptime_secs % 3600) // 60)
                with open("/proc/loadavg") as f:
                    load = f.read().strip()
                return f"Uptime: {days}d {hours}h {mins}m\nLoad avg: {load}"
            except:
                r = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
                return r.stdout.strip()

        elif name == "whoami":
            import pwd
            user = pwd.getpwuid(os.getuid())
            groups = subprocess.run(["groups"], capture_output=True, text=True, timeout=5).stdout.strip()
            return f"User: {user.pw_name}\nUID: {user.pw_uid}\nGID: {user.pw_gid}\nHome: {user.pw_dir}\nShell: {user.pw_shell}\nGroups: {groups}"

        elif name == "hostname_info":
            hostname = platform.node()
            try:
                ip = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5).stdout.strip()
            except:
                ip = "N/A"
            return f"Hostname: {hostname}\nIP: {ip}"

        elif name == "os_version":
            lines = [f"System: {platform.system()}", f"Release: {platform.release()}", f"Version: {platform.version()}", f"Machine: {platform.machine()}", f"Processor: {platform.processor()}"]
            try:
                with open("/etc/os-release") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            lines.append(f"{k}: {v.strip('\"')}")
            except:
                pass
            return "\n".join(lines)

        elif name == "temp_dir":
            import tempfile
            td = tempfile.gettempdir()
            try:
                import shutil
                usage = shutil.disk_usage(td)
                return f"Temp dir: {td}\nFree: {usage.free // (1024**2)}MB"
            except:
                return f"Temp dir: {td}"

        elif name == "shell_info":
            shell = os.environ.get("SHELL", "unknown")
            path = os.environ.get("PATH", "")
            return f"Shell: {shell}\nPATH entries: {len(path.split(':'))}\nPATH:\n{path}"

        elif name == "python_info":
            lines = [
                f"Version: {platform.python_version()}",
                f"Implementation: {platform.python_implementation()}",
                f"Compiler: {platform.python_compiler()}",
                f"Executable: {platform.python_executable()}",
                f"Prefix: {platform.prefix}",
            ]
            try:
                import site
                lines.append(f"Site-packages: {site.getsitepackages()}")
            except:
                pass
            return "\n".join(lines)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
