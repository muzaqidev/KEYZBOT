"""Docker and container management tools."""

import subprocess, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "docker_ps", "description": "List Docker containers. Shows running or all containers.", "parameters": {"type": "object", "properties": {"all": {"type": "boolean", "description": "Show all containers including stopped (default false)"}, "filter": {"type": "string", "description": "Filter containers (e.g. 'status=running', 'name=web')"}}, "required": []}}},
    {"type": "function", "function": {"name": "docker_images", "description": "List Docker images.", "parameters": {"type": "object", "properties": {"filter": {"type": "string", "description": "Filter images (e.g. 'dangling=true')"}}, "required": []}}},
    {"type": "function", "function": {"name": "docker_run", "description": "Run a Docker container.", "parameters": {"type": "object", "properties": {"image": {"type": "string", "description": "Image name"}, "command": {"type": "string", "description": "Command to run inside container"}, "ports": {"type": "string", "description": "Port mappings (e.g. '8080:80,3000:3000')"}, "volumes": {"type": "string", "description": "Volume mounts (e.g. '/host:/container')"}, "env": {"type": "string", "description": "Environment variables as JSON (e.g. '{\"KEY\":\"val\"}')"}, "name": {"type": "string", "description": "Container name"}, "detach": {"type": "boolean", "description": "Run in background (default true)"}, "rm": {"type": "boolean", "description": "Remove container when stopped (default false)"}}, "required": ["image"]}}},
    {"type": "function", "function": {"name": "docker_exec", "description": "Execute a command inside a running container.", "parameters": {"type": "object", "properties": {"container": {"type": "string", "description": "Container name or ID"}, "command": {"type": "string", "description": "Command to execute"}}, "required": ["container", "command"]}}},
    {"type": "function", "function": {"name": "docker_logs", "description": "Get logs from a Docker container.", "parameters": {"type": "object", "properties": {"container": {"type": "string", "description": "Container name or ID"}, "tail": {"type": "integer", "description": "Number of last lines (default 100)"}, "follow": {"type": "boolean", "description": "Follow log output (default false)"}}, "required": ["container"]}}},
    {"type": "function", "function": {"name": "docker_stop", "description": "Stop a running container.", "parameters": {"type": "object", "properties": {"container": {"type": "string", "description": "Container name or ID"}}, "required": ["container"]}}},
    {"type": "function", "function": {"name": "docker_start", "description": "Start a stopped container.", "parameters": {"type": "object", "properties": {"container": {"type": "string", "description": "Container name or ID"}}, "required": ["container"]}}},
    {"type": "function", "function": {"name": "docker_rm", "description": "Remove a container.", "parameters": {"type": "object", "properties": {"container": {"type": "string", "description": "Container name or ID"}, "force": {"type": "boolean", "description": "Force remove running container (default false)"}}, "required": ["container"]}}},
    {"type": "function", "function": {"name": "docker_build", "description": "Build a Docker image from a Dockerfile.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Build context directory"}, "tag": {"type": "string", "description": "Image tag (e.g. 'myapp:latest')"}, "dockerfile": {"type": "string", "description": "Dockerfile name (default 'Dockerfile')"}}, "required": ["path", "tag"]}}},
    {"type": "function", "function": {"name": "docker_compose", "description": "Run docker-compose commands (up, down, ps, logs, build).", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["up", "down", "ps", "logs", "build", "restart", "pull"], "description": "Compose action"}, "path": {"type": "string", "description": "Directory with docker-compose.yml (default: current dir)"}, "service": {"type": "string", "description": "Specific service name"}, "detach": {"type": "boolean", "description": "Run in background for 'up' (default true)"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "docker_inspect", "description": "Inspect a Docker container or image. Returns detailed JSON info.", "parameters": {"type": "object", "properties": {"target": {"type": "string", "description": "Container/image name or ID"}}, "required": ["target"]}}},
    {"type": "function", "function": {"name": "docker_prune", "description": "Clean up unused Docker resources (containers, images, volumes, networks).", "parameters": {"type": "object", "properties": {"type": {"type": "string", "enum": ["all", "containers", "images", "volumes", "networks"], "description": "What to prune (default 'all')"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        def run_docker(cmd_list):
            return subprocess.run(cmd_list, capture_output=True, text=True, timeout=60)

        if name == "docker_ps":
            cmd = ["docker", "ps", "--format", "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}"]
            if args.get("all"):
                cmd.insert(2, "-a")
            if args.get("filter"):
                cmd += ["--filter", args["filter"]]
            r = run_docker(cmd)
            return r.stdout or r.stderr or "(no containers)"

        elif name == "docker_images":
            cmd = ["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"]
            if args.get("filter"):
                cmd += ["--filter", args["filter"]]
            r = run_docker(cmd)
            return r.stdout or r.stderr or "(no images)"

        elif name == "docker_run":
            cmd = ["docker", "run"]
            if args.get("detach", True):
                cmd.append("-d")
            if args.get("rm"):
                cmd.append("--rm")
            if args.get("name"):
                cmd += ["--name", args["name"]]
            if args.get("ports"):
                for p in args["ports"].split(","):
                    cmd += ["-p", p.strip()]
            if args.get("volumes"):
                for v in args["volumes"].split(","):
                    cmd += ["-v", v.strip()]
            if args.get("env"):
                for k, v in json.loads(args["env"]).items():
                    cmd += ["-e", f"{k}={v}"]
            cmd.append(args["image"])
            if args.get("command"):
                cmd += args["command"].split()
            r = run_docker(cmd)
            return r.stdout.strip() or r.stderr.strip()

        elif name == "docker_exec":
            cmd = ["docker", "exec", args["container"]] + args["command"].split()
            r = run_docker(cmd)
            return r.stdout or r.stderr or "(no output)"

        elif name == "docker_logs":
            cmd = ["docker", "logs", "--tail", str(args.get("tail", 100))]
            if args.get("follow"):
                cmd.append("-f")
            cmd.append(args["container"])
            r = run_docker(cmd)
            return r.stdout or r.stderr or "(no logs)"

        elif name == "docker_stop":
            r = run_docker(["docker", "stop", args["container"]])
            return r.stdout.strip() or f"Stopped {args['container']}"

        elif name == "docker_start":
            r = run_docker(["docker", "start", args["container"]])
            return r.stdout.strip() or f"Started {args['container']}"

        elif name == "docker_rm":
            cmd = ["docker", "rm"]
            if args.get("force"):
                cmd.append("-f")
            cmd.append(args["container"])
            r = run_docker(cmd)
            return r.stdout.strip() or f"Removed {args['container']}"

        elif name == "docker_build":
            cmd = ["docker", "build", "-t", args["tag"]]
            if args.get("dockerfile"):
                cmd += ["-f", args["dockerfile"]]
            cmd.append(args["path"])
            r = run_docker(cmd)
            return r.stdout[-3000:] if r.stdout else r.stderr[-3000:]

        elif name == "docker_compose":
            action = args["action"]
            path = args.get("path", ".")
            cmd = ["docker-compose", "-f", f"{path}/docker-compose.yml"]
            if action == "up":
                cmd.append("up")
                if args.get("detach", True):
                    cmd.append("-d")
            elif action == "down":
                cmd.append("down")
            elif action == "build":
                cmd.append("build")
            elif action == "restart":
                cmd.append("restart")
            elif action == "pull":
                cmd.append("pull")
            elif action == "ps":
                cmd.append("ps")
            elif action == "logs":
                cmd += ["logs", "--tail", "100"]
            if args.get("service"):
                cmd.append(args["service"])
            r = run_docker(cmd)
            return r.stdout or r.stderr or "(no output)"

        elif name == "docker_inspect":
            r = run_docker(["docker", "inspect", args["target"]])
            try:
                data = json.loads(r.stdout)
                return json.dumps(data[0], indent=2)[:5000]
            except:
                return r.stdout or r.stderr

        elif name == "docker_prune":
            ptype = args.get("type", "all")
            if ptype == "all":
                r = run_docker(["docker", "system", "prune", "-f"])
            elif ptype == "containers":
                r = run_docker(["docker", "container", "prune", "-f"])
            elif ptype == "images":
                r = run_docker(["docker", "image", "prune", "-f"])
            elif ptype == "volumes":
                r = run_docker(["docker", "volume", "prune", "-f"])
            elif ptype == "networks":
                r = run_docker(["docker", "network", "prune", "-f"])
            else:
                return f"Unknown prune type: {ptype}"
            return r.stdout.strip() or r.stderr.strip() or "Pruned"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
