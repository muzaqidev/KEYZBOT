"""Package management tools for pip, npm, apt, and system packages."""

import subprocess

TOOL_DEFS = [
    {"type": "function", "function": {"name": "pip_install", "description": "Install Python packages using pip.", "parameters": {"type": "object", "properties": {"packages": {"type": "string", "description": "Package name(s) to install (space-separated)"}, "upgrade": {"type": "boolean", "description": "Upgrade if already installed (default false)"}, "requirements": {"type": "string", "description": "Path to requirements.txt file"}}, "required": []}}},
    {"type": "function", "function": {"name": "pip_uninstall", "description": "Uninstall Python packages.", "parameters": {"type": "object", "properties": {"packages": {"type": "string", "description": "Package name(s) to uninstall (space-separated)"}}, "required": ["packages"]}}},
    {"type": "function", "function": {"name": "pip_list", "description": "List installed Python packages.", "parameters": {"type": "object", "properties": {"outdated": {"type": "boolean", "description": "Show only outdated packages (default false)"}, "format": {"type": "string", "enum": ["columns", "freeze", "json"], "description": "Output format (default columns)"}}, "required": []}}},
    {"type": "function", "function": {"name": "pip_show", "description": "Show details about an installed Python package.", "parameters": {"type": "object", "properties": {"package": {"type": "string", "description": "Package name"}}, "required": ["package"]}}},
    {"type": "function", "function": {"name": "npm_install", "description": "Install Node.js packages using npm.", "parameters": {"type": "object", "properties": {"packages": {"type": "string", "description": "Package name(s) to install"}, "global": {"type": "boolean", "description": "Install globally (default false)"}, "dev": {"type": "boolean", "description": "Install as devDependency (default false)"}, "path": {"type": "string", "description": "Project directory (default: current dir)"}}, "required": []}}},
    {"type": "function", "function": {"name": "npm_uninstall", "description": "Uninstall Node.js packages.", "parameters": {"type": "object", "properties": {"packages": {"type": "string", "description": "Package name(s) to uninstall"}, "path": {"type": "string", "description": "Project directory"}}, "required": ["packages"]}}},
    {"type": "function", "function": {"name": "npm_list", "description": "List installed Node.js packages.", "parameters": {"type": "object", "properties": {"global": {"type": "boolean", "description": "List global packages (default false)"}, "depth": {"type": "integer", "description": "Dependency depth (default 0)"}}, "required": []}}},
    {"type": "function", "function": {"name": "npm_run", "description": "Run an npm script from package.json.", "parameters": {"type": "object", "properties": {"script": {"type": "string", "description": "Script name (e.g. 'build', 'test', 'start')"}, "path": {"type": "string", "description": "Project directory"}}, "required": ["script"]}}},
    {"type": "function", "function": {"name": "apt_install", "description": "Install system packages using apt (Linux/Termux).", "parameters": {"type": "object", "properties": {"packages": {"type": "string", "description": "Package name(s) to install (space-separated)"}, "update_first": {"type": "boolean", "description": "Run apt update first (default false)"}}, "required": ["packages"]}}},
    {"type": "function", "function": {"name": "apt_search", "description": "Search for available packages in apt.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "pkg_info", "description": "Show info about an installed system package.", "parameters": {"type": "object", "properties": {"package": {"type": "string", "description": "Package name"}}, "required": ["package"]}}},
    {"type": "function", "function": {"name": "pip_freeze", "description": "Export installed packages as requirements.txt format.", "parameters": {"type": "object", "properties": {"output": {"type": "string", "description": "Output file path (omit to print)"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        def run(cmd_list, cwd=None):
            return subprocess.run(cmd_list, capture_output=True, text=True, timeout=120, cwd=cwd)

        if name == "pip_install":
            cmd = ["pip", "install"]
            if args.get("upgrade"):
                cmd.append("--upgrade")
            if args.get("requirements"):
                cmd += ["-r", args["requirements"]]
            elif args.get("packages"):
                cmd += args["packages"].split()
            else:
                return "Error: specify packages or requirements file"
            r = run(cmd)
            return (r.stdout + r.stderr)[-3000:]

        elif name == "pip_uninstall":
            cmd = ["pip", "uninstall", "-y"] + args["packages"].split()
            r = run(cmd)
            return r.stdout or r.stderr

        elif name == "pip_list":
            cmd = ["pip", "list"]
            if args.get("outdated"):
                cmd.append("--outdated")
            fmt = args.get("format", "columns")
            if fmt == "freeze":
                cmd = ["pip", "freeze"]
            elif fmt == "json":
                cmd += ["--format=json"]
            r = run(cmd)
            return r.stdout[:5000] or r.stderr

        elif name == "pip_show":
            r = run(["pip", "show", args["package"]])
            return r.stdout or f"Package '{args['package']}' not found"

        elif name == "npm_install":
            cmd = ["npm", "install"]
            if args.get("global"):
                cmd.append("-g")
            if args.get("dev"):
                cmd.append("--save-dev")
            cmd += args.get("packages", "").split()
            cwd = args.get("path", work_dir)
            r = run(cmd, cwd=cwd)
            return (r.stdout + r.stderr)[-3000:]

        elif name == "npm_uninstall":
            cmd = ["npm", "uninstall"] + args["packages"].split()
            cwd = args.get("path", work_dir)
            r = run(cmd, cwd=cwd)
            return r.stdout or r.stderr

        elif name == "npm_list":
            cmd = ["npm", "list"]
            if args.get("global"):
                cmd.append("-g")
            cmd += ["--depth", str(args.get("depth", 0))]
            r = run(cmd)
            return r.stdout[:5000] or r.stderr

        elif name == "npm_run":
            cmd = ["npm", "run", args["script"]]
            cwd = args.get("path", work_dir)
            r = run(cmd, cwd=cwd)
            return (r.stdout + r.stderr)[-3000:]

        elif name == "apt_install":
            if args.get("update_first"):
                run(["apt", "update", "-y"])
            cmd = ["apt", "install", "-y"] + args["packages"].split()
            r = run(cmd)
            return (r.stdout + r.stderr)[-3000:]

        elif name == "apt_search":
            r = run(["apt", "search", args["query"]])
            return r.stdout[:5000] or r.stderr or "(no results)"

        elif name == "pkg_info":
            r = run(["dpkg", "-s", args["package"]])
            if r.returncode != 0:
                r = run(["apt", "show", args["package"]])
            return r.stdout[:3000] or f"Package '{args['package']}' not found"

        elif name == "pip_freeze":
            r = run(["pip", "freeze"])
            if args.get("output"):
                with open(args["output"], "w") as f:
                    f.write(r.stdout)
                return f"Saved to {args['output']}"
            return r.stdout[:5000]

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
