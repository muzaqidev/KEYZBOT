"""File operations: read, write, edit."""

import os

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's contents. Returns numbered lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                    "offset": {"type": "integer", "description": "Line number to start from (1-indexed)"},
                    "limit": {"type": "integer", "description": "Max lines to read (default 2000)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates or overwrites.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing an exact string with new content. Read the file first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the file"},
                    "old_string": {"type": "string", "description": "Exact string to find and replace"},
                    "new_string": {"type": "string", "description": "Replacement string"},
                    "replace_all": {"type": "boolean", "description": "Replace all occurrences (default false, replaces first only)"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.js'). Returns paths sorted by modification time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern to match"},
                    "path": {"type": "string", "description": "Directory to search in (default: current dir)"},
                    "head_limit": {"type": "integer", "description": "Max results to return (default 100)"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep_files",
            "description": "Search file contents using regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "File or directory to search in"},
                    "include": {"type": "string", "description": "File glob to filter (e.g. '*.py')"},
                    "context": {"type": "integer", "description": "Lines of context before and after match (default 0)"},
                    "case_insensitive": {"type": "boolean", "description": "Case insensitive search (default true)"},
                    "output_mode": {"type": "string", "description": "Output mode: 'content' (default), 'files_with_matches', 'count'"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories in a path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list"},
                    "hidden": {"type": "boolean", "description": "Include hidden files (default false)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tree",
            "description": "Show directory tree structure. Great for understanding project layout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root directory to show tree for"},
                    "depth": {"type": "integer", "description": "Max depth (default 3)"},
                    "hidden": {"type": "boolean", "description": "Include hidden files (default false)"}
                },
                "required": ["path"]
            }
        }
    }
]

def _tool_name():
    return [d["function"]["name"] for d in TOOL_DEFS]

def execute(name, args, work_dir=None):
    """Execute a file operation tool."""
    if name == "read_file":
        return _read(args)
    elif name == "write_file":
        return _write(args)
    elif name == "edit_file":
        return _edit(args)
    elif name == "glob_files":
        return _glob(args, work_dir)
    elif name == "grep_files":
        return _grep(args, work_dir)
    elif name == "list_dir":
        return _list_dir(args)
    elif name == "tree":
        return _tree(args)
    return f"Unknown tool: {name}"

def _read(args):
    path = args.get("path", "")
    offset = args.get("offset", 1)
    limit = args.get("limit", 2000)

    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    if os.path.isdir(path):
        return f"Error: {path} is a directory, not a file. Use list_dir instead."

    # Auto-detect image files and redirect to image tool
    ext = os.path.splitext(path)[1].lower()
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
        from tools import image
        return image.read_image(path)

    try:
        with open(path, "r", errors="replace") as f:
            lines = f.readlines()

        start = max(0, offset - 1)
        end = min(len(lines), start + limit)
        selected = lines[start:end]

        # Number lines
        numbered = []
        for i, line in enumerate(selected, start=start + 1):
            numbered.append(f"{i:>6}\t{line.rstrip()}")

        header = f"File: {path} ({len(lines)} total lines)"
        if offset > 1 or limit < len(lines):
            header += f" (showing {start+1}-{end})"

        return header + "\n" + "\n".join(numbered)

    except Exception as e:
        return f"Error reading file: {e}"

def _write(args):
    path = args.get("path", "")
    content = args.get("content", "")

    if not path:
        return "Error: No path provided"

    try:
        # Check if file exists for diff
        old_content = None
        if os.path.exists(path):
            with open(path, "r", errors="replace") as f:
                old_content = f.read()

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

        lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        result = f"Written {len(content)} bytes ({lines} lines) to {path}"

        # Show diff if overwriting existing file
        if old_content is not None and old_content != content:
            import difflib
            old_lines = old_content.splitlines(keepends=True)
            new_lines = content.splitlines(keepends=True)
            diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{os.path.basename(path)}", tofile=f"b/{os.path.basename(path)}", n=3))
            diff_str = "".join(diff)
            if diff_str:
                if len(diff_str) > 3000:
                    diff_str = diff_str[:3000] + "\n... (diff truncated)"
                result += f"\n\n{diff_str}"
        return result
    except Exception as e:
        return f"Error writing file: {e}"

def _edit(args):
    path = args.get("path", "")
    old = args.get("old_string", "")
    new = args.get("new_string", "")
    replace_all = args.get("replace_all", False)

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    try:
        with open(path, "r") as f:
            content = f.read()

        count = content.count(old)
        if count == 0:
            return f"Error: String not found in {path}. Make sure it matches exactly (including whitespace)."
        if count > 1 and not replace_all:
            lines = content.split('\n')
            match_lines = []
            for i, line in enumerate(lines, 1):
                if old in line:
                    match_lines.append(f"  line {i}: {line.rstrip()[:80]}")
            match_info = "\n".join(match_lines[:10])
            if len(match_lines) > 10:
                match_info += f"\n  ... and {len(match_lines) - 10} more"
            return f"Error: Found {count} matches in {path}. Provide a more unique string or set replace_all=true.\nMatches:\n{match_info}"

        if replace_all:
            new_content = content.replace(old, new)
            replaced = count
        else:
            new_content = content.replace(old, new, 1)
            replaced = 1

        with open(path, "w") as f:
            f.write(new_content)

        # Generate unified diff
        import difflib
        old_lines = content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{os.path.basename(path)}", tofile=f"b/{os.path.basename(path)}", n=3))
        diff_str = "".join(diff)

        result = f"Edited {path}: replaced {replaced} occurrence(s), {len(old)} chars with {len(new)} chars"
        if diff_str:
            # Truncate large diffs
            if len(diff_str) > 3000:
                diff_str = diff_str[:3000] + "\n... (diff truncated)"
            result += f"\n\n{diff_str}"
        return result
    except Exception as e:
        return f"Error editing file: {e}"

def _glob(args, work_dir=None):
    from pathlib import Path
    import fnmatch

    pattern = args.get("pattern", "")
    search = args.get("path", "") or work_dir or "."
    head_limit = args.get("head_limit", 100)

    if not pattern:
        return "Error: No pattern provided"

    try:
        root = Path(search)
        if not root.exists():
            return f"Error: Directory not found: {search}"

        matches = []
        for p in root.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(root))
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(p.name, pattern):
                    matches.append(p)

        # Sort by modification time (newest first)
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if not matches:
            return f"No files matching '{pattern}' in {search}"

        result = f"Found {len(matches)} file(s) matching '{pattern}':\n"
        for m in matches[:head_limit]:
            result += f"  {m}\n"
        if len(matches) > head_limit:
            result += f"  ... and {len(matches) - head_limit} more\n"
        return result.strip()
    except Exception as e:
        return f"Error: {e}"

def _grep(args, work_dir=None):
    import re
    from pathlib import Path

    pattern = args.get("pattern", "")
    search = args.get("path", "") or work_dir or "."
    include = args.get("include", "")
    context = args.get("context", 0)
    case_insensitive = args.get("case_insensitive", True)
    output_mode = args.get("output_mode", "content")

    if not pattern:
        return "Error: No pattern provided"

    try:
        flags = re.IGNORECASE if case_insensitive else 0
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Error: Invalid regex: {e}"

    try:
        root = Path(search)
        if not root.exists():
            return f"Error: Path not found: {search}"

        matches = []
        match_files = set()
        match_count = 0
        files_to_search = []

        if root.is_file():
            files_to_search = [root]
        else:
            for p in root.rglob("*"):
                if not p.is_file():
                    continue
                if p.stat().st_size > 1_000_000:  # Skip files > 1MB
                    continue
                if include:
                    import fnmatch
                    if not fnmatch.fnmatch(p.name, include):
                        continue
                files_to_search.append(p)

        for fpath in files_to_search:
            try:
                with open(fpath, "r", errors="replace") as f:
                    lines = f.readlines()

                file_matches = []
                for i, line in enumerate(lines):
                    if regex.search(line):
                        file_matches.append(i)
                        match_count += 1

                if file_matches:
                    match_files.add(str(fpath))
                    rel = str(fpath)
                    if work_dir and rel.startswith(work_dir):
                        rel = rel[len(work_dir)+1:]

                    if output_mode == "content":
                        for idx in file_matches:
                            # Add context lines
                            start = max(0, idx - context)
                            end = min(len(lines), idx + context + 1)
                            for ci in range(start, end):
                                prefix = f"{rel}:{ci+1}: "
                                if ci == idx:
                                    matches.append(f"{prefix}{lines[ci].rstrip()}")
                                elif context > 0:
                                    matches.append(f"{prefix}{lines[ci].rstrip()}")
                            if context > 0 and idx != file_matches[-1]:
                                matches.append("  --")
            except Exception:
                continue

        if output_mode == "files_with_matches":
            if not match_files:
                return f"No files with matches for '{pattern}'"
            result = f"Files with matches ({len(match_files)}):\n"
            for f in sorted(match_files):
                result += f"  {f}\n"
            return result.strip()

        if output_mode == "count":
            return f"Total: {match_count} match(es) in {len(match_files)} file(s)"

        # Default: content mode
        if not matches:
            return f"No matches for '{pattern}' in {search}"

        result = f"Found {match_count} match(es):\n"
        for m in matches[:200]:
            result += f"  {m}\n"
        if len(matches) > 200:
            result += f"  ... and {len(matches) - 200} more lines\n"
        return result.strip()
    except Exception as e:
        return f"Error: {e}"

def _tree(args):
    """Show directory tree structure."""
    path = args.get("path", ".")
    max_depth = args.get("depth", 3)
    show_hidden = args.get("hidden", False)

    if not os.path.exists(path):
        return f"Error: Path not found: {path}"
    if not os.path.isdir(path):
        return f"Error: {path} is not a directory"

    lines = [f"{path}/"]
    _dirs = 0
    _files = 0

    def _walk(dir_path, prefix="", depth=0):
        nonlocal _dirs, _files
        if depth >= max_depth:
            return
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            lines.append(f"{prefix}└── [permission denied]")
            return
        except Exception:
            return

        if not show_hidden:
            entries = [e for e in entries if not e.startswith(".")]

        for i, entry in enumerate(entries):
            full = os.path.join(dir_path, entry)
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            if os.path.isdir(full):
                _dirs += 1
                lines.append(f"{prefix}{connector}{entry}/")
                extension = "    " if is_last else "│   "
                _walk(full, prefix + extension, depth + 1)
            else:
                _files += 1
                size = os.path.getsize(full)
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.0f}KB"
                else:
                    size_str = f"{size/1024/1024:.1f}MB"
                lines.append(f"{prefix}{connector}{entry}  ({size_str})")

    _walk(path)
    lines.append(f"\n{_dirs} directories, {_files} files")
    return "\n".join(lines)

def _list_dir(args):
    path = args.get("path", ".")
    show_hidden = args.get("hidden", False)

    if not os.path.exists(path):
        return f"Error: Path not found: {path}"
    if not os.path.isdir(path):
        return f"Error: {path} is not a directory"

    try:
        entries = sorted(os.listdir(path))
        if not show_hidden:
            entries = [e for e in entries if not e.startswith(".")]
        if not entries:
            return f"Directory is empty: {path}"

        result = f"Contents of {path}:\n"
        dirs = []
        files = []
        for e in entries:
            full = os.path.join(path, e)
            if os.path.isdir(full):
                dirs.append(f"  {e}/")
            else:
                size = os.path.getsize(full)
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.1f}KB"
                else:
                    size_str = f"{size/1024/1024:.1f}MB"
                files.append(f"  {e}  ({size_str})")

        for d in dirs:
            result += d + "\n"
        for f in files:
            result += f + "\n"

        return result.strip()
    except Exception as e:
        return f"Error: {e}"
