"""Linter and test runner tools."""

import os, subprocess

# ─── Linter Tool ─────────────────────────────────────────────────────────────

LINTER_COMMANDS = {
    "eslint": {"cmd": "npx eslint", "ext": [".js", ".jsx", ".ts", ".tsx"], "config": [".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "eslint.config.js"]},
    "pylint": {"cmd": "pylint", "ext": [".py"], "config": [".pylintrc", "pylintrc"]},
    "mypy": {"cmd": "mypy", "ext": [".py"], "config": ["mypy.ini", "pyproject.toml"]},
    "flake8": {"cmd": "flake8", "ext": [".py"], "config": [".flake8", "setup.cfg"]},
    "ruff": {"cmd": "ruff check", "ext": [".py"], "config": ["ruff.toml", "pyproject.toml"]},
    "rustfmt": {"cmd": "cargo fmt --check", "ext": [".rs"], "config": ["rustfmt.toml"]},
    "golangci-lint": {"cmd": "golangci-lint run", "ext": [".go"], "config": [".golangci.yml"]},
}

# ─── Test Runner Tool ────────────────────────────────────────────────────────

TEST_COMMANDS = {
    "pytest": {"cmd": "python3 -m pytest", "config": ["pytest.ini", "pyproject.toml", "setup.cfg"]},
    "jest": {"cmd": "npx jest", "config": ["jest.config.js", "jest.config.ts", "package.json"]},
    "vitest": {"cmd": "npx vitest run", "config": ["vitest.config.js", "vitest.config.ts"]},
    "cargo-test": {"cmd": "cargo test", "config": ["Cargo.toml"]},
    "go-test": {"cmd": "go test ./...", "config": ["go.mod"]},
    "phpunit": {"cmd": "phpunit", "config": ["phpunit.xml"]},
    "ruby": {"cmd": "bundle exec rspec", "config": ["Gemfile"]},
}

TEST_FILE_PATTERNS = {
    "pytest": "test_*.py",
    "jest": "*.test.{js,ts,jsx,tsx}",
    "vitest": "*.test.{js,ts,jsx,tsx}",
    "cargo-test": "*.rs (mod tests)",
    "go-test": "*_test.go",
}


def _detect_linter(path="."):
    """Auto-detect which linter to use."""
    for name, info in LINTER_COMMANDS.items():
        for cfg in info["config"]:
            if os.path.exists(os.path.join(path, cfg)):
                return name
    return None


def _detect_test_runner(path="."):
    """Auto-detect which test runner to use."""
    for name, info in TEST_COMMANDS.items():
        for cfg in info["config"]:
            if os.path.exists(os.path.join(path, cfg)):
                return name
    return None


def run_lint(args, work_dir=None):
    """Run linter on a file or directory."""
    target = args.get("path", ".")
    linter = args.get("linter", "") or _detect_linter(work_dir or ".")

    if not linter:
        # Try to detect from file extension
        ext = os.path.splitext(target)[1] if os.path.isfile(target) else ""
        ext_map = {".py": "ruff", ".js": "eslint", ".ts": "eslint", ".jsx": "eslint", ".tsx": "eslint", ".rs": "rustfmt", ".go": "golangci-lint"}
        linter = ext_map.get(ext, "ruff")

    info = LINTER_COMMANDS.get(linter)
    if not info:
        return f"Unknown linter: {linter}. Available: {', '.join(LINTER_COMMANDS.keys())}"

    cmd = f"{info['cmd']} {target}"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=work_dir or ".")
        output = result.stdout + result.stderr
        if not output.strip():
            return f"Linter ({linter}): No issues found in {target}"
        # Truncate large output
        if len(output) > 5000:
            output = output[:5000] + "\n... (truncated)"
        return f"Linter ({linter}) output:\n{output}"
    except subprocess.TimeoutExpired:
        return f"Linter ({linter}) timed out after 60s"
    except FileNotFoundError:
        return f"Linter '{linter}' not installed. Install it first."


def run_tests(args, work_dir=None):
    """Run tests using detected or specified test runner."""
    runner = args.get("runner", "") or _detect_test_runner(work_dir or ".")
    target = args.get("path", "")
    pattern = args.get("pattern", "")
    verbose = args.get("verbose", True)

    if not runner:
        return "No test runner detected. Specify 'runner' parameter (pytest, jest, vitest, cargo-test, go-test)."

    info = TEST_COMMANDS.get(runner)
    if not info:
        return f"Unknown runner: {runner}. Available: {', '.join(TEST_COMMANDS.keys())}"

    cmd = info["cmd"]
    if verbose and runner in ("pytest", "jest", "vitest"):
        cmd += " -v"
    if pattern:
        cmd += f" {pattern}"
    elif target:
        cmd += f" {target}"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120, cwd=work_dir or ".")
        output = result.stdout + result.stderr
        status = "PASS" if result.returncode == 0 else "FAIL"
        # Truncate large output
        if len(output) > 8000:
            output = output[:4000] + "\n... (truncated) ...\n" + output[-4000:]
        return f"Tests ({runner}) [{status}]:\n{output}"
    except subprocess.TimeoutExpired:
        return f"Tests ({runner}) timed out after 120s"
    except FileNotFoundError:
        return f"Test runner '{runner}' not installed."


TOOL_NAMES = {"lint", "test_runner"}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "lint",
            "description": "Run a linter (ESLint, Pylint, mypy, ruff, etc.) on a file or directory. Auto-detects linter from project config files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or directory to lint (default: current directory)"},
                    "linter": {"type": "string", "description": "Linter to use (eslint, pylint, mypy, flake8, ruff, rustfmt, golangci-lint). Auto-detected if omitted."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_runner",
            "description": "Run project tests using the appropriate test runner. Auto-detects runner from project config (pytest, jest, vitest, cargo test, go test).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Test file or directory to run (default: all tests)"},
                    "runner": {"type": "string", "description": "Test runner (pytest, jest, vitest, cargo-test, go-test). Auto-detected if omitted."},
                    "pattern": {"type": "string", "description": "Test name pattern or file pattern to filter"},
                    "verbose": {"type": "boolean", "description": "Verbose output (default: true)"}
                }
            }
        }
    }
]


def execute(name, args, work_dir=None, bot=None):
    if name == "lint":
        return run_lint(args, work_dir)
    elif name == "test_runner":
        return run_tests(args, work_dir)
    return f"Unknown tool: {name}"
