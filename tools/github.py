"""GitHub API integration — PR, issues, remote repo interaction."""

import os, json, subprocess

def _gh(args_str, work_dir=None):
    """Run gh CLI command and return output."""
    try:
        result = subprocess.run(
            f"gh {args_str}", shell=True,
            capture_output=True, text=True, timeout=30,
            cwd=work_dir or "."
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            return f"Error: {err or output}"
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: gh command timed out"
    except FileNotFoundError:
        return "Error: gh CLI not installed. Install with: apt install gh"


def gh_pr(args, work_dir=None):
    """Manage pull requests."""
    action = args.get("action", "list")
    if action == "list":
        return _gh("pr list --limit 20", work_dir)
    elif action == "view":
        num = args.get("number", "")
        return _gh(f"pr view {num}", work_dir)
    elif action == "create":
        title = args.get("title", "")
        body = args.get("body", "")
        base = args.get("base", "")
        cmd = f'pr create --title "{title}" --body "{body}"'
        if base:
            cmd += f" --base {base}"
        return _gh(cmd, work_dir)
    elif action == "diff":
        num = args.get("number", "")
        return _gh(f"pr diff {num}", work_dir)
    elif action == "checks":
        num = args.get("number", "")
        return _gh(f"pr checks {num}", work_dir)
    elif action == "merge":
        num = args.get("number", "")
        method = args.get("method", "merge")
        return _gh(f"pr merge {num} --{method}", work_dir)
    elif action == "review":
        num = args.get("number", "")
        event = args.get("event", "comment")
        body = args.get("body", "")
        cmd = f"pr review {num} --{event}"
        if body:
            cmd += f' --body "{body}"'
        return _gh(cmd, work_dir)
    return f"Unknown PR action: {action}"


def gh_issue(args, work_dir=None):
    """Manage issues."""
    action = args.get("action", "list")
    if action == "list":
        return _gh("issue list --limit 20", work_dir)
    elif action == "view":
        num = args.get("number", "")
        return _gh(f"issue view {num}", work_dir)
    elif action == "create":
        title = args.get("title", "")
        body = args.get("body", "")
        labels = args.get("labels", "")
        cmd = f'issue create --title "{title}" --body "{body}"'
        if labels:
            cmd += f" --label {labels}"
        return _gh(cmd, work_dir)
    elif action == "close":
        num = args.get("number", "")
        return _gh(f"issue close {num}", work_dir)
    elif action == "comment":
        num = args.get("number", "")
        body = args.get("body", "")
        return _gh(f'issue comment {num} --body "{body}"', work_dir)
    return f"Unknown issue action: {action}"


def gh_repo(args, work_dir=None):
    """Repository operations."""
    action = args.get("action", "info")
    if action == "info":
        return _gh("repo view", work_dir)
    elif action == "clone":
        url = args.get("url", "")
        return _gh(f"repo clone {url}", work_dir)
    elif action == "fork":
        return _gh("repo fork --clone=false", work_dir)
    elif action == "list":
        owner = args.get("owner", "")
        return _gh(f"repo list {owner} --limit 20", work_dir)
    return f"Unknown repo action: {action}"


def gh_gist(args, work_dir=None):
    """Gist operations."""
    action = args.get("action", "list")
    if action == "list":
        return _gh("gist list --limit 10", work_dir)
    elif action == "create":
        file = args.get("file", "")
        desc = args.get("description", "")
        return _gh(f'gist create "{file}" --desc "{desc}"', work_dir)
    return f"Unknown gist action: {action}"


def gh_api(args, work_dir=None):
    """Raw GitHub API calls."""
    endpoint = args.get("endpoint", "")
    method = args.get("method", "GET")
    data = args.get("data", "")
    cmd = f"api {endpoint} --method {method}"
    if data:
        cmd += f" -f {data}"
    return _gh(cmd, work_dir)


TOOL_NAMES = {"github"}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "github",
            "description": "GitHub operations via gh CLI: manage PRs, issues, repos, gists, and API calls. Requires gh CLI authenticated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource": {"type": "string", "enum": ["pr", "issue", "repo", "gist", "api"], "description": "GitHub resource type"},
                    "action": {"type": "string", "description": "Action: pr=list/view/create/diff/checks/merge/review, issue=list/view/create/close/comment, repo=info/clone/fork/list, gist=list/create, api=endpoint"},
                    "number": {"type": "string", "description": "PR or issue number"},
                    "title": {"type": "string", "description": "Title for new PR or issue"},
                    "body": {"type": "string", "description": "Body/description text"},
                    "base": {"type": "string", "description": "Base branch for PR"},
                    "method": {"type": "string", "description": "HTTP method (for api) or merge method (squash/merge/rebase)"},
                    "event": {"type": "string", "description": "Review event (approve/comment/request-changes)"},
                    "labels": {"type": "string", "description": "Comma-separated labels for issues"},
                    "url": {"type": "string", "description": "URL for clone"},
                    "owner": {"type": "string", "description": "Owner for repo list"},
                    "file": {"type": "string", "description": "File path for gist create"},
                    "endpoint": {"type": "string", "description": "API endpoint (for api resource)"},
                    "data": {"type": "string", "description": "API request data"}
                },
                "required": ["resource"]
            }
        }
    }
]


def execute(name, args, work_dir=None, bot=None):
    resource = args.get("resource", "")
    if resource == "pr":
        return gh_pr(args, work_dir)
    elif resource == "issue":
        return gh_issue(args, work_dir)
    elif resource == "repo":
        return gh_repo(args, work_dir)
    elif resource == "gist":
        return gh_gist(args, work_dir)
    elif resource == "api":
        return gh_api(args, work_dir)
    return f"Unknown resource: {resource}. Use: pr, issue, repo, gist, api"
