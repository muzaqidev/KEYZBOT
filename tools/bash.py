"""Bash tool - execute shell commands."""

import subprocess, os

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute a bash command and return its output. Use for running programs, system commands, testing, installing packages, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "description": {
                    "type": "string",
                    "description": "Clear, concise description of what this command does (shown to user)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 120)"
                },
                "run_in_background": {
                    "type": "boolean",
                    "description": "Run command in background, return immediately with process ID"
                }
            },
            "required": ["command"]
        }
    }
}

def execute(args, work_dir=None):
    """Execute a bash command."""
    from core.sandbox import check_command, get_timeout, SandboxViolation
    from core import permissions as perms

    cmd = args.get("command", "")
    timeout = args.get("timeout", 120)
    description = args.get("description", "")
    run_in_background = args.get("run_in_background", False)
    cwd = work_dir or os.getcwd()

    if not cmd:
        return "Error: No command provided"

    # Sandbox check
    sandbox_mode = perms.get_sandbox_mode()
    try:
        is_safe, reason = check_command(cmd, sandbox_mode)
        if not is_safe and sandbox_mode == "warn":
            # Return warning as part of output
            pass  # Will prepend warning
    except SandboxViolation as e:
        return f"Sandbox blocked: {e}"

    timeout = get_timeout(timeout)

    # Background execution — delegate to monitor module
    if run_in_background:
        from tools import monitor
        result = monitor.start(cmd, cwd)
        if description:
            return f"[{description}]\n{result}"
        return result

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += f"[stderr]\n{result.stderr}"
        if result.returncode != 0:
            if output:
                output += "\n"
            output += f"[exit code: {result.returncode}]"

        final = output.strip() or "(no output)"
        if description:
            return f"[{description}]\n{final}"
        return final

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"
