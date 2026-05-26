"""Cloud and DevOps tools — SSH, SCP, rsync, cloud CLIs."""

import subprocess, os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "ssh_exec", "description": "Execute a command on a remote server via SSH.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "user@host"}, "command": {"type": "string", "description": "Command to execute"}, "key": {"type": "string", "description": "SSH key file path"}, "port": {"type": "integer", "description": "SSH port (default 22)"}, "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}}, "required": ["host", "command"]}}},
    {"type": "function", "function": {"name": "scp_transfer", "description": "Copy files to/from a remote server via SCP.", "parameters": {"type": "object", "properties": {"source": {"type": "string", "description": "Source path (local or user@host:remote_path)"}, "destination": {"type": "string", "description": "Destination path"}, "key": {"type": "string", "description": "SSH key file"}, "port": {"type": "integer", "description": "SSH port (default 22)"}, "recursive": {"type": "boolean", "description": "Copy directories recursively (default false)"}}, "required": ["source", "destination"]}}},
    {"type": "function", "function": {"name": "rsync_sync", "description": "Sync directories using rsync. Supports local and remote.", "parameters": {"type": "object", "properties": {"source": {"type": "string", "description": "Source path"}, "destination": {"type": "string", "description": "Destination path"}, "exclude": {"type": "string", "description": "Exclude patterns (comma-separated)"}, "delete": {"type": "boolean", "description": "Delete files not in source (default false)"}, "dry_run": {"type": "boolean", "description": "Show what would be transferred (default false)"}}, "required": ["source", "destination"]}}},
    {"type": "function", "function": {"name": "aws_cli", "description": "Run AWS CLI commands.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "AWS CLI command (e.g. 's3 ls', 'ec2 describe-instances')"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "gcloud_cli", "description": "Run Google Cloud CLI commands.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "gcloud command"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "azure_cli", "description": "Run Azure CLI commands.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "az command"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "terraform_run", "description": "Run Terraform commands (init, plan, apply, destroy).", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["init", "plan", "apply", "destroy", "output", "state"], "description": "Terraform action"}, "path": {"type": "string", "description": "Terraform directory"}, "var_file": {"type": "string", "description": "Variables file path"}, "auto_approve": {"type": "boolean", "description": "Auto-approve apply/destroy (default false)"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "ansible_run", "description": "Run Ansible playbooks or ad-hoc commands.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "ansible or ansible-playbook command"}, "inventory": {"type": "string", "description": "Inventory file path"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "kubectl_run", "description": "Run kubectl commands for Kubernetes management.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "kubectl command (e.g. 'get pods', 'apply -f deploy.yaml')"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "docker_hub_search", "description": "Search Docker Hub for images.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search query"}, "limit": {"type": "integer", "description": "Max results (default 10)"}}, "required": ["query"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        def run(cmd_list, timeout=30):
            return subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)

        if name == "ssh_exec":
            cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
            if args.get("port"):
                cmd += ["-p", str(args["port"])]
            if args.get("key"):
                cmd += ["-i", args["key"]]
            cmd += [args["host"], args["command"]]
            r = run(cmd, timeout=args.get("timeout", 30))
            return r.stdout or r.stderr or "(no output)"

        elif name == "scp_transfer":
            cmd = ["scp", "-o", "StrictHostKeyChecking=no"]
            if args.get("port"):
                cmd += ["-P", str(args["port"])]
            if args.get("key"):
                cmd += ["-i", args["key"]]
            if args.get("recursive"):
                cmd.append("-r")
            cmd += [args["source"], args["destination"]]
            r = run(cmd, timeout=120)
            return r.stdout or r.stderr or "Transfer complete"

        elif name == "rsync_sync":
            cmd = ["rsync", "-avz", "--progress"]
            if args.get("exclude"):
                for p in args["exclude"].split(","):
                    cmd += ["--exclude", p.strip()]
            if args.get("delete"):
                cmd.append("--delete")
            if args.get("dry_run"):
                cmd.append("--dry-run")
            cmd += [args["source"], args["destination"]]
            r = run(cmd, timeout=300)
            return r.stdout[-5000:] or r.stderr[-5000:]

        elif name == "aws_cli":
            cmd = ["aws"] + args["command"].split()
            r = run(cmd, timeout=60)
            return r.stdout[:5000] or r.stderr[:5000]

        elif name == "gcloud_cli":
            cmd = ["gcloud"] + args["command"].split()
            r = run(cmd, timeout=60)
            return r.stdout[:5000] or r.stderr[:5000]

        elif name == "azure_cli":
            cmd = ["az"] + args["command"].split()
            r = run(cmd, timeout=60)
            return r.stdout[:5000] or r.stderr[:5000]

        elif name == "terraform_run":
            action = args["action"]
            path = args.get("path", ".")
            cmd = ["terraform", action]
            if action in ("apply", "destroy") and args.get("auto_approve"):
                cmd.append("-auto-approve")
            if args.get("var_file"):
                cmd += ["-var-file", args["var_file"]]
            r = run(cmd, timeout=300, cwd=path)
            return r.stdout[-5000:] or r.stderr[-5000:]

        elif name == "ansible_run":
            cmd = args["command"].split()
            if args.get("inventory"):
                cmd += ["-i", args["inventory"]]
            r = run(cmd, timeout=120)
            return r.stdout[-5000:] or r.stderr[-5000:]

        elif name == "kubectl_run":
            cmd = ["kubectl"] + args["command"].split()
            r = run(cmd, timeout=60)
            return r.stdout[:5000] or r.stderr[:5000]

        elif name == "docker_hub_search":
            import requests
            query = args["query"]
            limit = args.get("limit", 10)
            resp = requests.get(f"https://hub.docker.com/v2/search/repositories/?query={query}&page_size={limit}", timeout=10)
            data = resp.json()
            lines = []
            for r in data.get("results", []):
                stars = r.get("star_count", 0)
                pulls = r.get("pull_count", 0)
                lines.append(f"{r['repo_name']} ({stars} stars, {pulls} pulls) — {r.get('short_description', '')[:80]}")
            return "\n".join(lines) or "(no results)"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
