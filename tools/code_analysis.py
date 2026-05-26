"""Code analysis, search, and transformation tools."""

import os, re, json, subprocess

TOOL_DEFS = [
    {"type": "function", "function": {"name": "code_search", "description": "Search for code patterns across a project using regex. Returns matching lines with file and line number.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern to search for"}, "path": {"type": "string", "description": "Directory or file to search in"}, "include": {"type": "string", "description": "File glob filter (e.g. '*.py')"}, "context": {"type": "integer", "description": "Lines of context (default 0)"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "code_count", "description": "Count lines of code, comments, and blanks per file and total.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory or file to count"}, "include": {"type": "string", "description": "File glob filter (e.g. '*.py')"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_functions", "description": "Find all function/method definitions in Python or JavaScript files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory to scan"}, "pattern": {"type": "string", "description": "Optional function name filter"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_classes", "description": "Find all class definitions in Python files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory to scan"}, "pattern": {"type": "string", "description": "Optional class name filter"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_imports", "description": "Find all import statements in Python files. Shows which modules are used.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory to scan"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_unused_imports", "description": "Find potentially unused imports in Python files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file to analyze"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "complexity_check", "description": "Check cyclomatic complexity of Python functions. Identifies overly complex code.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file to analyze"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "code_diff", "description": "Compare two files and show differences.", "parameters": {"type": "object", "properties": {"file1": {"type": "string", "description": "First file path"}, "file2": {"type": "string", "description": "Second file path"}}, "required": ["file1", "file2"]}}},
    {"type": "function", "function": {"name": "format_code", "description": "Auto-format Python code using autopep8 or JavaScript using prettier.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File to format"}, "formatter": {"type": "string", "enum": ["autopep8", "black", "prettier", "rustfmt"], "description": "Formatter to use (auto-detected)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "check_syntax", "description": "Check Python file for syntax errors without running it.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file to check"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_strings", "description": "Find all string literals in Python files. Useful for finding hardcoded values.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory to scan"}, "min_length": {"type": "integer", "description": "Minimum string length (default 5)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "find_todos", "description": "Find all TODO, FIXME, HACK, XXX comments in code.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory or file to scan"}, "include": {"type": "string", "description": "File glob filter"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "dependency_list", "description": "List all third-party dependencies from requirements.txt, package.json, or Cargo.toml.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "ast_dump", "description": "Dump the AST (Abstract Syntax Tree) of a Python file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file to parse"}, "indent": {"type": "integer", "description": "Indentation level (default 2)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rename_symbol", "description": "Rename a function or variable across all files in a project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}, "old_name": {"type": "string", "description": "Current name"}, "new_name": {"type": "string", "description": "New name"}, "include": {"type": "string", "description": "File glob filter (e.g. '*.py')"}}, "required": ["path", "old_name", "new_name"]}}},
    {"type": "function", "function": {"name": "duplicate_finder", "description": "Find duplicate or near-duplicate code blocks in a project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory to scan"}, "min_lines": {"type": "integer", "description": "Minimum lines per block (default 5)"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "code_search":
            path = args.get("path", ".")
            include = args.get("include", "")
            context = args.get("context", 0)
            cmd = ["grep", "-rn", "-E", args["pattern"]]
            if context:
                cmd += ["-C", str(context)]
            if include:
                cmd += ["--include", include]
            cmd.append(path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.stdout[:8000] or "(no matches)"

        elif name == "code_count":
            path = args.get("path", ".")
            ext = args.get("include", "")
            total_code = total_comment = total_blank = 0
            lines_out = []
            targets = []
            if os.path.isfile(path):
                targets = [path]
            else:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
                    for f in files:
                        if ext and not f.endswith(ext.lstrip("*")):
                            continue
                        targets.append(os.path.join(root, f))
            for fp in targets[:200]:
                try:
                    with open(fp) as f:
                        lines = f.readlines()
                except:
                    continue
                code = comment = blank = 0
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                    elif stripped.startswith("#") or stripped.startswith("//"):
                        comment += 1
                    else:
                        code += 1
                total_code += code
                total_comment += comment
                total_blank += blank
                lines_out.append(f"{fp}: {code} code, {comment} comment, {blank} blank")
            lines_out.append(f"\nTotal: {total_code} code, {total_comment} comment, {total_blank} blank ({total_code + total_comment + total_blank} lines)")
            return "\n".join(lines_out[:100])

        elif name == "find_functions":
            path = args.get("path", ".")
            pattern = args.get("pattern", "")
            regex = r"^(\s*)def\s+(\w+)" if not pattern else rf"^(\s*)def\s+({pattern}\w*)"
            cmd = ["grep", "-rn", "-E", regex, path, "--include=*.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout[:5000] or "(no functions found)"

        elif name == "find_classes":
            path = args.get("path", ".")
            pattern = args.get("pattern", "")
            regex = r"^class\s+(\w+)" if not pattern else rf"^class\s+({pattern}\w*)"
            cmd = ["grep", "-rn", "-E", regex, path, "--include=*.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout[:5000] or "(no classes found)"

        elif name == "find_imports":
            path = args.get("path", ".")
            cmd = ["grep", "-rn", "-E", r"^(import |from .+ import )", path, "--include=*.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split("\n")[:200]
            modules = set()
            for line in lines:
                if line.startswith("from "):
                    mod = line.split()[1].split(".")[0]
                    modules.add(mod)
                elif line.startswith("import "):
                    mod = line.split()[1].split(".")[0]
                    modules.add(mod)
            return f"Modules used ({len(modules)}):\n{', '.join(sorted(modules))}\n\nDetails:\n{result.stdout[:5000]}"

        elif name == "find_unused_imports":
            path = args["path"]
            with open(path) as f:
                content = f.read()
            imports = re.findall(r"^(?:from\s+(\S+)|import\s+(\S+))", content, re.MULTILINE)
            unused = []
            for mod_tuple in imports:
                mod = mod_tuple[0] or mod_tuple[1]
                name_part = mod.split(".")[-1]
                count = content.count(name_part) - 1
                if count <= 0:
                    unused.append(mod)
            return f"Potentially unused imports:\n" + "\n".join(f"  - {u}" for u in unused) if unused else "All imports appear to be used."

        elif name == "complexity_check":
            path = args["path"]
            with open(path) as f:
                content = f.read()
            functions = re.findall(r"def\s+(\w+)\s*\(", content)
            results = []
            for func in functions:
                func_match = re.search(rf"def\s+{func}\s*\(.*?\)(.*?)(?=\ndef\s|\Z)", content, re.DOTALL)
                if func_match:
                    body = func_match.group(1)
                    branches = len(re.findall(r"\b(if|elif|for|while|except|and|or)\b", body))
                    complexity = branches + 1
                    level = "LOW" if complexity <= 5 else "MEDIUM" if complexity <= 10 else "HIGH"
                    results.append(f"{func}: complexity={complexity} ({level})")
            return "\n".join(results) or "(no functions found)"

        elif name == "code_diff":
            result = subprocess.run(["diff", "-u", args["file1"], args["file2"]], capture_output=True, text=True, timeout=10)
            return result.stdout[:8000] or "(files are identical)"

        elif name == "format_code":
            path = args["path"]
            formatter = args.get("formatter", "")
            if not formatter:
                formatter = "black" if path.endswith(".py") else "prettier"
            if formatter == "autopep8":
                result = subprocess.run(["autopep8", "-i", path], capture_output=True, text=True, timeout=30)
            elif formatter == "black":
                result = subprocess.run(["black", "-q", path], capture_output=True, text=True, timeout=30)
            elif formatter == "prettier":
                result = subprocess.run(["prettier", "--write", path], capture_output=True, text=True, timeout=30)
            elif formatter == "rustfmt":
                result = subprocess.run(["rustfmt", path], capture_output=True, text=True, timeout=30)
            else:
                return f"Unknown formatter: {formatter}"
            return f"Formatted {path} with {formatter}" + (f"\n{result.stderr}" if result.stderr else "")

        elif name == "check_syntax":
            import py_compile
            try:
                py_compile.compile(args["path"], doraise=True)
                return f"Syntax OK: {args['path']}"
            except py_compile.PyCompileError as e:
                return f"Syntax Error: {e}"

        elif name == "find_strings":
            path = args.get("path", ".")
            min_len = args.get("min_length", 5)
            cmd = ["grep", "-rn", "-oE", rf'"[^"]{{{min_len},}}"', path, "--include=*.py"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout[:5000] or "(no strings found)"

        elif name == "find_todos":
            path = args.get("path", ".")
            include = args.get("include", "")
            cmd = ["grep", "-rn", "-iE", r"(TODO|FIXME|HACK|XXX|OPTIMIZE|NOTE):", path]
            if include:
                cmd += ["--include", include]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout[:5000] or "(no TODOs found)"

        elif name == "dependency_list":
            path = args.get("path", ".")
            results = []
            req = os.path.join(path, "requirements.txt")
            if os.path.exists(req):
                with open(req) as f:
                    results.append(f"[requirements.txt]\n{f.read().strip()}")
            pkg = os.path.join(path, "package.json")
            if os.path.exists(pkg):
                with open(pkg) as f:
                    data = json.load(f)
                deps = data.get("dependencies", {})
                dev = data.get("devDependencies", {})
                lines = [f"[package.json]"]
                for k, v in deps.items():
                    lines.append(f"  {k}: {v}")
                if dev:
                    lines.append("  [devDependencies]")
                    for k, v in dev.items():
                        lines.append(f"  {k}: {v}")
                results.append("\n".join(lines))
            cargo = os.path.join(path, "Cargo.toml")
            if os.path.exists(cargo):
                with open(cargo) as f:
                    results.append(f"[Cargo.toml]\n{f.read().strip()}")
            return "\n\n".join(results) or "(no dependency files found)"

        elif name == "ast_dump":
            import ast
            with open(args["path"]) as f:
                tree = ast.parse(f.read())
            indent = args.get("indent", 2)
            return ast.dump(tree, indent=indent)[:8000]

        elif name == "rename_symbol":
            path = args["path"]
            old = args["old_name"]
            new = args["new_name"]
            include = args.get("include", "*.py")
            cmd = ["find", path, "-name", include, "-exec", "sed", "-i", f"s/{old}/{new}/g", "{}", "+"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return f"Renamed '{old}' -> '{new}' in {path}"

        elif name == "duplicate_finder":
            path = args.get("path", ".")
            min_lines = args.get("min_lines", 5)
            blocks = {}
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
                for fn in files:
                    if not fn.endswith(('.py', '.js', '.ts')):
                        continue
                    fp = os.path.join(root, fn)
                    try:
                        with open(fp) as f:
                            lines = [l.strip() for l in f if l.strip()]
                    except:
                        continue
                    for i in range(len(lines) - min_lines):
                        block = tuple(lines[i:i + min_lines])
                        key = hash(block)
                        if key in blocks:
                            blocks[key].append((fp, i + 1))
                        else:
                            blocks[key] = [(fp, i + 1)]
            dupes = {k: v for k, v in blocks.items() if len(v) > 1}
            if not dupes:
                return "No duplicate blocks found."
            results = []
            for i, (k, locs) in enumerate(list(dupes.items())[:20]):
                results.append(f"Duplicate #{i+1}:")
                for fp, line in locs[:5]:
                    results.append(f"  {fp}:{line}")
            return "\n".join(results)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
