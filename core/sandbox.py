"""Sandbox mode for safe bash execution."""

import re

# Dangerous patterns that should be blocked in sandbox mode
BLOCKED_PATTERNS = [
    r'\brm\s+(-[rfR]*\s+)*(\/|~|\*)',
    r'\bmkfs\b',
    r'\bdd\s+.*of=',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bpoweroff\b',
    r'\bkill\s+-9\s+1\b',
    r'\bkillall\b',
    r'\biptables\b',
    r'\bchmod\s+777\b',
    r'\bchown\s+root\b',
    r'\bvisudo\b',
    r'\buseradd\b',
    r'\buserdel\b',
    r'\bgroupadd\b',
    r'\bpasswd\b',
    r'\bsu\s+',
    r'\bsudo\s+',
    r'\bcurl\b.*\|\s*(ba)?sh',
    r'\bwget\b.*\|\s*(ba)?sh',
    r'>\s*\/dev\/sd',
    r'>\s*\/dev\/nvme',
    r'\bnc\s+.*-e',
    r'\bncat\b.*-e',
    r'\bsocat\b',
    r'\bpython[23]?\s+-c.*import\s+os.*system',
    r'\bbase64\s+.*\|\s*(ba)?sh',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\/proc\/self\/',
    r'\/etc\/passwd',
    r'\/etc\/shadow',
]

# Safe commands that are always allowed
SAFE_COMMANDS = [
    'ls', 'cat', 'head', 'tail', 'wc', 'grep', 'find', 'echo', 'printf',
    'pwd', 'whoami', 'date', 'which', 'file', 'stat', 'du', 'df',
    'cd', 'mkdir', 'touch', 'cp', 'mv', 'ln',
    'git', 'python3', 'python', 'node', 'npm', 'npx', 'pip', 'pip3',
    'cargo', 'go', 'rustc', 'gcc', 'g++', 'make', 'cmake',
    'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    'diff', 'patch', 'sort', 'uniq', 'cut', 'awk', 'sed', 'tr',
    'ps', 'top', 'htop', 'free', 'uptime',
    'curl', 'wget', 'ssh', 'scp', 'rsync',
    'pytest', 'jest', 'eslint', 'pylint', 'mypy', 'ruff',
    'gh', 'docker', 'docker-compose',
]

# Max execution time in seconds
MAX_TIMEOUT = 120
DEFAULT_TIMEOUT = 30


class SandboxViolation(Exception):
    """Raised when a command violates sandbox rules."""
    pass


def check_command(cmd_str, sandbox_mode="off"):
    """Check if a command is safe to execute.

    Args:
        cmd_str: The command string to check
        sandbox_mode: "off", "warn", or "block"

    Returns:
        (is_safe, reason) tuple
    """
    if sandbox_mode == "off":
        return True, ""

    cmd = cmd_str.strip()
    if not cmd:
        return True, ""

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            reason = f"Blocked: matches dangerous pattern ({pattern})"
            if sandbox_mode == "block":
                raise SandboxViolation(reason)
            return False, reason

    # Check for rm -rf on important directories
    if re.search(r'\brm\b.*-[a-zA-Z]*r[a-zA-Z]*f', cmd):
        # Check what's being removed
        targets = re.findall(r'\brm\b.*?(?:\/[^\s]*)', cmd)
        for t in targets:
            if t.rstrip('/') in ('/', '/root', '/home', '/sdcard', '/data'):
                reason = f"Blocked: recursive force delete on {t}"
                if sandbox_mode == "block":
                    raise SandboxViolation(reason)
                return False, reason

    return True, ""


def get_timeout(args_timeout):
    """Get safe timeout value."""
    if not args_timeout:
        return DEFAULT_TIMEOUT
    try:
        t = int(args_timeout)
        return min(max(t, 1), MAX_TIMEOUT)
    except (ValueError, TypeError):
        return DEFAULT_TIMEOUT


def format_violation(cmd, reason):
    """Format a sandbox violation message."""
    return f"Sandbox violation: {reason}\nCommand: {cmd[:200]}"
