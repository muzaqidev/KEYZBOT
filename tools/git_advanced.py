"""Advanced Git tools — beyond basic operations."""

import subprocess, os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "git_blame", "description": "Show who last modified each line of a file.", "parameters": {"type": "object", "properties": {"file": {"type": "string", "description": "File path"}, "line_range": {"type": "string", "description": "Line range (e.g. '10-20')"}}, "required": ["file"]}}},
    {"type": "function", "function": {"name": "git_search", "description": "Search git history for commits matching a pattern.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Search pattern"}, "path": {"type": "string", "description": "Git repo path (default: current dir)"}, "author": {"type": "string", "description": "Filter by author"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "git_diff_stat", "description": "Show diff statistics between commits or branches.", "parameters": {"type": "object", "properties": {"from_ref": {"type": "string", "description": "From commit/branch (default: HEAD~1)"}, "to_ref": {"type": "string", "description": "To commit/branch (default: HEAD)"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_stash_list", "description": "List all git stashes with details.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Git repo path"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_stash_apply", "description": "Apply a git stash by index.", "parameters": {"type": "object", "properties": {"index": {"type": "integer", "description": "Stash index (default 0)"}, "pop": {"type": "boolean", "description": "Pop (remove) stash after applying (default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_cherry_pick", "description": "Cherry-pick a commit onto current branch.", "parameters": {"type": "object", "properties": {"commit": {"type": "string", "description": "Commit hash to cherry-pick"}}, "required": ["commit"]}}},
    {"type": "function", "function": {"name": "git_rebase", "description": "Rebase current branch onto another.", "parameters": {"type": "object", "properties": {"onto": {"type": "string", "description": "Branch/commit to rebase onto"}, "interactive": {"type": "boolean", "description": "Interactive rebase (default false)"}}, "required": ["onto"]}}},
    {"type": "function", "function": {"name": "git_tag", "description": "Create, list, or delete git tags.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["create", "list", "delete"], "description": "Tag action"}, "name": {"type": "string", "description": "Tag name (for create/delete)"}, "message": {"type": "string", "description": "Tag message (for annotated tags)"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "git_contributors", "description": "List contributors by commit count.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Git repo path"}, "since": {"type": "string", "description": "Since date (e.g. '2024-01-01')"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_file_history", "description": "Show commit history for a specific file.", "parameters": {"type": "object", "properties": {"file": {"type": "string", "description": "File path"}, "limit": {"type": "integer", "description": "Max entries (default 20)"}}, "required": ["file"]}}},
    {"type": "function", "function": {"name": "git_restore", "description": "Restore file(s) to a specific commit state.", "parameters": {"type": "object", "properties": {"files": {"type": "array", "items": {"type": "string"}, "description": "Files to restore"}, "commit": {"type": "string", "description": "Commit hash (default: HEAD)"}}, "required": ["files"]}}},
    {"type": "function", "function": {"name": "git_clean", "description": "Remove untracked files from working directory.", "parameters": {"type": "object", "properties": {"dry_run": {"type": "boolean", "description": "Show what would be deleted (default true)"}, "force": {"type": "boolean", "description": "Actually delete (default false)"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_hooks_list", "description": "List git hooks in the repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Git repo path"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        def run(cmd, cwd=None):
            return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd or work_dir)

        if name == "git_blame":
            cmd = ["git", "blame"]
            if args.get("line_range"):
                cmd += ["-L", args["line_range"]]
            cmd.append(args["file"])
            r = run(cmd)
            return r.stdout[:5000] or r.stderr

        elif name == "git_search":
            cmd = ["git", "log", f"--grep={args['pattern']}", "--oneline"]
            if args.get("author"):
                cmd += ["--author", args["author"]]
            path = args.get("path", work_dir)
            r = run(cmd, cwd=path)
            return r.stdout[:5000] or "(no matches)"

        elif name == "git_diff_stat":
            fr = args.get("from_ref", "HEAD~1")
            to = args.get("to_ref", "HEAD")
            r = run(["git", "diff", "--stat", fr, to])
            return r.stdout[:3000] or r.stderr or "(no differences)"

        elif name == "git_stash_list":
            r = run(["git", "stash", "list", "--format=%gd: %gs (%ci)"])
            return r.stdout or "(no stashes)"

        elif name == "git_stash_apply":
            index = args.get("index", 0)
            cmd = ["git", "stash", "pop" if args.get("pop") else "apply", f"stash@{{{index}}}"]
            r = run(cmd)
            return r.stdout or r.stderr

        elif name == "git_cherry_pick":
            r = run(["git", "cherry-pick", args["commit"]])
            return r.stdout or r.stderr

        elif name == "git_rebase":
            cmd = ["git", "rebase", args["onto"]]
            r = run(cmd)
            return r.stdout or r.stderr

        elif name == "git_tag":
            action = args["action"]
            if action == "list":
                r = run(["git", "tag", "-l", "--format=%(refname:short) %(creatordate:short) %(subject)"])
                return r.stdout or "(no tags)"
            elif action == "create":
                cmd = ["git", "tag"]
                if args.get("message"):
                    cmd += ["-a", args["name"], "-m", args["message"]]
                else:
                    cmd.append(args["name"])
                r = run(cmd)
                return r.stdout or f"Tag '{args['name']}' created"
            elif action == "delete":
                r = run(["git", "tag", "-d", args["name"]])
                return r.stdout or f"Tag '{args['name']}' deleted"

        elif name == "git_contributors":
            cmd = ["git", "shortlog", "-sn", "--no-merges"]
            if args.get("since"):
                cmd += ["--since", args["since"]]
            r = run(cmd, cwd=args.get("path", work_dir))
            return r.stdout or "(no contributors)"

        elif name == "git_file_history":
            limit = args.get("limit", 20)
            r = run(["git", "log", f"--oneline", f"-{limit}", "--follow", args["file"]])
            return r.stdout or "(no history)"

        elif name == "git_restore":
            commit = args.get("commit", "HEAD")
            cmd = ["git", "restore", f"--source={commit}"] + args["files"]
            r = run(cmd)
            return r.stdout or f"Restored {len(args['files'])} files to {commit}"

        elif name == "git_clean":
            cmd = ["git", "clean"]
            if args.get("force"):
                cmd.append("-f")
            else:
                cmd.append("-n")
            if args.get("dry_run", True) and not args.get("force"):
                cmd.append("-n")
            r = run(cmd)
            return r.stdout or "(nothing to clean)"

        elif name == "git_hooks_list":
            path = args.get("path", work_dir) or "."
            hooks_dir = os.path.join(path, ".git", "hooks")
            if not os.path.isdir(hooks_dir):
                return "(no hooks directory)"
            hooks = [f for f in os.listdir(hooks_dir) if not f.endswith(".sample")]
            samples = [f for f in os.listdir(hooks_dir) if f.endswith(".sample")]
            lines = []
            if hooks:
                lines.append("Active hooks:")
                lines.extend(f"  {h}" for h in hooks)
            if samples:
                lines.append(f"Available templates ({len(samples)}):")
                lines.extend(f"  {s}" for s in samples[:10])
            return "\n".join(lines) or "(no hooks)"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
