"""Git operations — commit, branch, PR, worktree."""

import subprocess, os, shlex

def _run(args, work_dir=None):
    """Run git command safely using list args (no shell injection)."""
    if isinstance(args, str):
        args = shlex.split(args)
    r = subprocess.run(args, capture_output=True, text=True, cwd=work_dir or os.getcwd(), timeout=30)
    return (r.stdout + r.stderr).strip()

def git_status(work_dir=None):
    return _run(["git", "status"], work_dir)

def git_diff(work_dir=None):
    return _run(["git", "diff"], work_dir)

def git_log(n=10, work_dir=None):
    return _run(["git", "log", "--oneline", f"-{n}"], work_dir)

def git_commit(message, files=None, work_dir=None):
    if files:
        for f in files:
            _run(["git", "add", f], work_dir)
    else:
        _run(["git", "add", "-A"], work_dir)
    return _run(["git", "commit", "-m", message], work_dir)

def git_branch(name=None, work_dir=None):
    if name:
        return _run(["git", "checkout", "-b", name], work_dir)
    return _run(["git", "branch", "-a"], work_dir)

def git_checkout(branch, work_dir=None):
    return _run(["git", "checkout", branch], work_dir)

def git_merge(branch, work_dir=None):
    return _run(["git", "merge", branch], work_dir)

def git_push(remote="origin", branch=None, work_dir=None):
    b = branch or _run(["git", "branch", "--show-current"], work_dir)
    return _run(["git", "push", remote, b], work_dir)

def git_pull(work_dir=None):
    return _run(["git", "pull"], work_dir)

def git_stash(action="push", work_dir=None):
    if action == "pop":
        return _run(["git", "stash", "pop"], work_dir)
    return _run(["git", "stash"], work_dir)

def git_worktree(action, path=None, branch=None, work_dir=None):
    if action == "add" and path:
        cmd = ["git", "worktree", "add", path]
        if branch:
            cmd.extend(["-b", branch])
        return _run(cmd, work_dir)
    elif action == "remove" and path:
        return _run(["git", "worktree", "remove", path], work_dir)
    elif action == "list":
        return _run(["git", "worktree", "list"], work_dir)
    return "Usage: worktree add/remove/list [path] [branch]"

# Tool definitions
TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "git",
            "description": "Run git operations. Actions: status, diff, log, commit, branch, checkout, merge, push, pull, stash, worktree.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Git action: status, diff, log, commit, branch, checkout, merge, push, pull, stash, worktree"},
                    "args": {"type": "string", "description": "Arguments for the action (message for commit, branch name, etc.)"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Files to stage (for commit)"}
                },
                "required": ["action"]
            }
        }
    }
]

TOOL_NAMES = {"git"}

def execute(name, args, work_dir=None):
    if name != "git":
        return f"Unknown tool: {name}"
    action = args.get("action", "status")
    a = args.get("args", "")
    files = args.get("files")

    if action == "status":
        return git_status(work_dir)
    elif action == "diff":
        return git_diff(work_dir)
    elif action == "log":
        return git_log(int(a) if a else 10, work_dir)
    elif action == "commit":
        return git_commit(a or "Update", files, work_dir)
    elif action == "branch":
        return git_branch(a or None, work_dir)
    elif action == "checkout":
        return git_checkout(a, work_dir)
    elif action == "merge":
        return git_merge(a, work_dir)
    elif action == "push":
        return git_push(work_dir=work_dir)
    elif action == "pull":
        return git_pull(work_dir)
    elif action == "stash":
        return git_stash(a or "push", work_dir)
    elif action == "worktree":
        parts = a.split() if a else ["list"]
        return git_worktree(parts[0], parts[1] if len(parts) > 1 else None, parts[2] if len(parts) > 2 else None, work_dir)
    return f"Unknown git action: {action}"
