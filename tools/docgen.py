"""Documentation generation tools — API docs, diagrams, wikis, README."""

import os, json, re

TOOL_DEFS = [
    {"type": "function", "function": {"name": "generate_api_docs", "description": "Generate API documentation from source code or OpenAPI spec.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Source file or directory"}, "format": {"type": "string", "enum": ["markdown", "html", "json"], "description": "Output format (default markdown)"}, "style": {"type": "string", "enum": ["rest", "flask", "fastapi", "express", "auto"], "description": "Framework style (default auto)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_tree_docs", "description": "Generate project documentation from directory tree and file structure.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}, "ignore": {"type": "string", "description": "Patterns to ignore (comma-separated)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_class_docs", "description": "Generate class documentation from Python files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file or directory"}, "format": {"type": "string", "enum": ["markdown", "html"], "description": "Output format (default markdown)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_rest_api", "description": "Generate REST API endpoint documentation from Flask/FastAPI/Express code.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Source file"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_diagram", "description": "Generate a Mermaid diagram from code structure or data.", "parameters": {"type": "object", "properties": {"type": {"type": "string", "enum": ["flowchart", "class", "sequence", "er", "dependency"], "description": "Diagram type"}, "path": {"type": "string", "description": "Source file or directory"}, "output": {"type": "string", "description": "Output .md file with embedded Mermaid"}}, "required": ["type", "path"]}}},
    {"type": "function", "function": {"name": "generate_changelog", "description": "Generate a formatted CHANGELOG.md from git history.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Git repository path"}, "since_tag": {"type": "string", "description": "Since which tag/commit"}, "output": {"type": "string", "description": "Output file (default: print)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_contributing", "description": "Generate a CONTRIBUTING.md guide for a project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}, "style": {"type": "string", "enum": ["minimal", "standard", "detailed"], "description": "Detail level (default standard)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_license", "description": "Generate a LICENSE file.", "parameters": {"type": "object", "properties": {"type": {"type": "string", "enum": ["mit", "apache2", "gpl3", "bsd2", "bsd3", "unlicense", "isc"], "description": "License type"}, "author": {"type": "string", "description": "Author name"}, "year": {"type": "string", "description": "Year (default current)"}}, "required": ["type", "author"]}}},
    {"type": "function", "function": {"name": "generate_env_docs", "description": "Generate documentation for environment variables used in a project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Source file or directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_test_docs", "description": "Generate test documentation from test files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Test file or directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_deps_docs", "description": "Generate dependency documentation with descriptions and licenses.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "generate_wiki", "description": "Generate a complete wiki structure for a project.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory"}, "output_dir": {"type": "string", "description": "Output directory for wiki files"}}, "required": ["path", "output_dir"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "generate_api_docs":
            path = args["path"]
            style = args.get("style", "auto")
            lines = ["# API Documentation\n"]
            if os.path.isfile(path):
                targets = [path]
            else:
                targets = []
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
                    for f in files:
                        if f.endswith(('.py', '.js', '.ts')):
                            targets.append(os.path.join(root, f))
            for fp in targets[:50]:
                try:
                    with open(fp) as f:
                        content = f.read()
                except:
                    continue
                # Find route decorators (@app.route, @router.get, app.get, router.get)
                routes = re.findall(r'@(?:app|router|api)\.(get|post|put|delete|patch)\(["\']([^"\']+)', content)
                routes += re.findall(r'@(?:app|router|api)\.(route)\(["\']([^"\']+)', content)
                if routes:
                    lines.append(f"\n## {os.path.basename(fp)}\n")
                    lines.append("| Method | Path | Description |")
                    lines.append("|--------|------|-------------|")
                    for method, path_str in routes:
                        lines.append(f"| {method.upper()} | `{path_str}` | — |")
                # Find functions with docstrings
                funcs = re.findall(r'def\s+(\w+)\s*\([^)]*\).*?(?:"""(.*?)""")?', content, re.DOTALL)
                if funcs:
                    lines.append(f"\n## Functions in {os.path.basename(fp)}\n")
                    for fname, doc in funcs:
                        if fname.startswith("_"):
                            continue
                        doc_clean = doc.strip().split("\n")[0] if doc else "—"
                        lines.append(f"- **{fname}()** — {doc_clean}")
            return "\n".join(lines) or "(no API endpoints found)"

        elif name == "generate_tree_docs":
            path = args["path"]
            ignore = set((args.get("ignore", "") + ",.git,node_modules,__pycache__,.venv,.pytest_cache").split(","))
            lines = [f"# Project: {os.path.basename(path)}\n"]
            lines.append("## Structure\n``````")
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ignore]
                level = root.replace(path, "").count(os.sep)
                indent = "  " * level
                lines.append(f"{indent}{os.path.basename(root)}/")
                sub_indent = "  " * (level + 1)
                for f in sorted(files)[:30]:
                    size = os.path.getsize(os.path.join(root, f))
                    lines.append(f"{sub_indent}{f} ({size}B)")
            lines.append("``````")
            # File type stats
            exts = {}
            for root, dirs, files in os.walk(path):
                for f in files:
                    ext = os.path.splitext(f)[1] or "(no ext)"
                    exts[ext] = exts.get(ext, 0) + 1
            lines.append("\n## File Types\n")
            for ext, count in sorted(exts.items(), key=lambda x: -x[1])[:15]:
                lines.append(f"- {ext}: {count}")
            return "\n".join(lines)

        elif name == "generate_class_docs":
            path = args["path"]
            lines = ["# Class Documentation\n"]
            targets = [path] if os.path.isfile(path) else []
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
                    for f in files:
                        if f.endswith('.py'):
                            targets.append(os.path.join(root, f))
            for fp in targets[:30]:
                with open(fp) as f:
                    content = f.read()
                classes = re.findall(r'class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:(.*?)(?=\nclass\s|\Z)', content, re.DOTALL)
                if classes:
                    lines.append(f"\n## {os.path.basename(fp)}\n")
                    for cname, bases, body in classes:
                        lines.append(f"### {cname}")
                        if bases:
                            lines.append(f"**Inherits:** {bases}")
                        # Methods
                        methods = re.findall(r'def\s+(\w+)\s*\([^)]*\)', body)
                        doc = re.search(r'"""(.*?)"""', body)
                        if doc:
                            lines.append(f"\n{doc.group(1).strip()}\n")
                        if methods:
                            lines.append("**Methods:**")
                            for m in methods:
                                if not m.startswith("__"):
                                    lines.append(f"- `{m}()`")
                        lines.append("")
            return "\n".join(lines) or "(no classes found)"

        elif name == "generate_rest_api":
            path = args["path"]
            with open(path) as f:
                content = f.read()
            lines = [f"# REST API: {os.path.basename(path)}\n"]
            # Find all routes
            routes = re.findall(r'@(?:app|router|api)\.(get|post|put|delete|patch)\(["\']([^"\']+)[^)]*\)\s*(?:async\s+)?def\s+(\w+)', content)
            if not routes:
                routes = re.findall(r'@(?:app|router|api)\.(route)\(["\']([^"\']+)[^)]*\)\s*(?:async\s+)?def\s+(\w+)', content)
            for method, path_str, func in routes:
                lines.append(f"### {method.upper()} `{path_str}`")
                lines.append(f"**Handler:** `{func}()`\n")
                # Find docstring for the function
                doc_match = re.search(rf'def\s+{func}\s*\([^)]*\).*?"""(.*?)"""', content, re.DOTALL)
                if doc_match:
                    lines.append(doc_match.group(1).strip())
                lines.append("")
            return "\n".join(lines) or "(no REST endpoints found)"

        elif name == "generate_diagram":
            dtype = args["type"]
            path = args["path"]
            output = args.get("output", "")
            lines = ["```mermaid"]
            if dtype == "flowchart":
                lines.append("graph TD")
                # Simple file dependency flow
                if os.path.isfile(path):
                    with open(path) as f:
                        content = f.read()
                    imports = re.findall(r'from\s+(\w+)\s+import|import\s+(\w+)', content)
                    base = os.path.splitext(os.path.basename(path))[0]
                    for mod, _ in imports:
                        if mod:
                            lines.append(f"  {base} --> {mod}")
                else:
                    for root, dirs, files in os.walk(path):
                        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]
                        parent = os.path.basename(root)
                        for f in files[:10]:
                            if f.endswith(('.py', '.js')):
                                lines.append(f"  {parent} --> {os.path.splitext(f)[0]}")
            elif dtype == "class":
                lines.append("classDiagram")
                if os.path.isfile(path):
                    targets = [path]
                else:
                    targets = []
                    for root, dirs, files in os.walk(path):
                        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]
                        for f in files:
                            if f.endswith('.py'):
                                targets.append(os.path.join(root, f))
                for fp in targets[:10]:
                    with open(fp) as f:
                        content = f.read()
                    classes = re.findall(r'class\s+(\w+)\s*(?:\(([^)]*)\))?', content)
                    for cname, bases in classes:
                        if bases:
                            for b in bases.split(","):
                                lines.append(f"  {b.strip()} <|-- {cname}")
                        methods = re.findall(rf'class\s+{cname}.*?def\s+(\w+)\s*\(', content, re.DOTALL)
                        lines.append(f"  class {cname} {{")
                        for m in methods[:5]:
                            if not m.startswith("__"):
                                lines.append(f"    +{m}()")
                        lines.append("  }")
            elif dtype == "sequence":
                lines.append("sequenceDiagram")
                lines.append("  participant User")
                lines.append("  participant API")
                lines.append("  participant DB")
                lines.append("  User->>API: Request")
                lines.append("  API->>DB: Query")
                lines.append("  DB-->>API: Result")
                lines.append("  API-->>User: Response")
            elif dtype == "dependency":
                lines.append("graph LR")
                if os.path.isdir(path):
                    req = os.path.join(path, "requirements.txt")
                    if os.path.exists(req):
                        with open(req) as f:
                            for line in f:
                                pkg = line.strip().split("==")[0].split(">=")[0].split("<=")[0]
                                if pkg and not pkg.startswith("#"):
                                    lines.append(f"  project --> {pkg}")
            lines.append("```")
            result = "\n".join(lines)
            if output:
                with open(output, "w") as f:
                    f.write(result)
                return f"Diagram saved to {output}"
            return result

        elif name == "generate_changelog":
            import subprocess
            path = args.get("path", ".")
            since = args.get("since_tag", "")
            cmd = ["git", "log", "--oneline", "--no-merges", "--format=%h %s (%an, %ad)", "--date=short"]
            if since:
                cmd.append(f"{since}..HEAD")
            else:
                cmd = cmd[:5] + ["-30"] + cmd[5:]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=path)
            commits = r.stdout.strip()
            if not commits:
                return "No commits found"
            lines = ["# Changelog\n"]
            features, fixes, other = [], [], []
            for line in commits.split("\n"):
                lower = line.lower()
                if any(w in lower for w in ["add", "feat", "new", "implement", "create"]):
                    features.append(line)
                elif any(w in lower for w in ["fix", "bug", "patch", "resolve", "correct"]):
                    fixes.append(line)
                else:
                    other.append(line)
            if features:
                lines.append("## Features\n")
                for f in features:
                    lines.append(f"- {f}")
                lines.append("")
            if fixes:
                lines.append("## Bug Fixes\n")
                for f in fixes:
                    lines.append(f"- {f}")
                lines.append("")
            if other:
                lines.append("## Other Changes\n")
                for o in other:
                    lines.append(f"- {o}")
            result = "\n".join(lines)
            output = args.get("output")
            if output:
                with open(output, "w") as f:
                    f.write(result)
                return f"Changelog saved to {output}"
            return result

        elif name == "generate_contributing":
            path = args.get("path", ".")
            style = args.get("style", "standard")
            lines = ["# Contributing\n", "Thank you for your interest in contributing!\n"]
            lines.append("## How to Contribute\n")
            lines.append("1. **Fork** this repository")
            lines.append("2. **Create** a feature branch (`git checkout -b feature/my-feature`)")
            lines.append("3. **Commit** your changes (`git commit -m 'Add my feature'`)")
            lines.append("4. **Push** to the branch (`git push origin feature/my-feature`)")
            lines.append("5. **Open** a Pull Request\n")
            if style in ("standard", "detailed"):
                lines.append("## Development Setup\n")
                lines.append("```bash")
                lines.append("git clone <repo-url>")
                lines.append("cd <project>")
                lines.append("pip install -r requirements.txt")
                lines.append("python -m pytest tests/")
                lines.append("```\n")
                lines.append("## Code Style\n")
                lines.append("- Follow PEP 8 for Python")
                lines.append("- Add tests for new features")
                lines.append("- Update documentation as needed\n")
            if style == "detailed":
                lines.append("## Pull Request Process\n")
                lines.append("1. Ensure all tests pass")
                lines.append("2. Update the README if needed")
                lines.append("3. Request review from a maintainer")
                lines.append("4. Squash commits before merge\n")
                lines.append("## Reporting Issues\n")
                lines.append("- Use the issue tracker")
                lines.append("- Include reproduction steps")
                lines.append("- Mention your OS and Python version\n")
            return "\n".join(lines)

        elif name == "generate_license":
            ltype = args["type"]
            author = args["author"]
            year = args.get("year", "2024-2026")
            templates = {
                "mit": f"""MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",
                "unlicense": """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute
this software, either in source code form or as a compiled binary, for any
purpose, commercial or non-commercial, and by any means.""",
            }
            return templates.get(ltype, f"License type '{ltype}' — see https://choosealicense.com/")

        elif name == "generate_env_docs":
            path = args["path"]
            targets = [path] if os.path.isfile(path) else []
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
                    for f in files:
                        if f.endswith(('.py', '.js', '.ts', '.env')):
                            targets.append(os.path.join(root, f))
            env_vars = set()
            for fp in targets[:100]:
                try:
                    with open(fp) as f:
                        content = f.read()
                    # os.environ.get("KEY"), os.environ["KEY"], process.env.KEY, env("KEY")
                    env_vars.update(re.findall(r'os\.environ\.get\(["\'](\w+)', content))
                    env_vars.update(re.findall(r'os\.environ\[["\'](\w+)', content))
                    env_vars.update(re.findall(r'process\.env\.(\w+)', content))
                    env_vars.update(re.findall(r'env\(["\'](\w+)', content))
                except:
                    continue
            if not env_vars:
                return "(no environment variables found)"
            lines = ["# Environment Variables\n", "| Variable | Description | Default |", "|----------|-------------|---------|"]
            for v in sorted(env_vars):
                lines.append(f"| `{v}` | — | — |")
            return "\n".join(lines)

        elif name == "generate_test_docs":
            path = args["path"]
            targets = [path] if os.path.isfile(path) else []
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]
                    for f in files:
                        if f.startswith("test_") and f.endswith(".py"):
                            targets.append(os.path.join(root, f))
            lines = ["# Test Documentation\n"]
            total_tests = 0
            for fp in targets[:30]:
                try:
                    with open(fp) as f:
                        content = f.read()
                except:
                    continue
                tests = re.findall(r'def\s+(test_\w+)', content)
                classes = re.findall(r'class\s+(Test\w+)', content)
                if tests:
                    lines.append(f"\n## {os.path.basename(fp)}\n")
                    if classes:
                        lines.append(f"**Test classes:** {', '.join(classes)}\n")
                    for t in tests:
                        lines.append(f"- `{t}()`")
                    total_tests += len(tests)
            lines.append(f"\n**Total tests: {total_tests}**")
            return "\n".join(lines) or "(no test files found)"

        elif name == "generate_deps_docs":
            path = args.get("path", ".")
            lines = ["# Dependencies\n"]
            req = os.path.join(path, "requirements.txt")
            if os.path.exists(req):
                lines.append("## Python (requirements.txt)\n")
                lines.append("| Package | Version | Description |")
                lines.append("|---------|---------|-------------|")
                with open(req) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            parts = line.split("==")
                            pkg = parts[0].split(">=")[0].split("<=")[0]
                            ver = parts[1] if len(parts) > 1 else "latest"
                            lines.append(f"| {pkg} | {ver} | — |")
            pkg = os.path.join(path, "package.json")
            if os.path.exists(pkg):
                with open(pkg) as f:
                    data = json.load(f)
                deps = data.get("dependencies", {})
                if deps:
                    lines.append("\n## Node.js (package.json)\n")
                    lines.append("| Package | Version | Description |")
                    lines.append("|---------|---------|-------------|")
                    for k, v in deps.items():
                        lines.append(f"| {k} | {v} | — |")
            return "\n".join(lines)

        elif name == "generate_wiki":
            path = args["path"]
            output_dir = args["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            # Generate multiple wiki pages
            pages = {}
            pages["Home.md"] = f"# {os.path.basename(path)} Wiki\n\nWelcome to the project documentation.\n"
            pages["Structure.md"] = execute("generate_tree_docs", {"path": path}, work_dir)
            pages["API.md"] = execute("generate_api_docs", {"path": path}, work_dir)
            pages["Dependencies.md"] = execute("generate_deps_docs", {"path": path}, work_dir)
            pages["Environment.md"] = execute("generate_env_docs", {"path": path}, work_dir)
            pages["Tests.md"] = execute("generate_test_docs", {"path": path}, work_dir)
            for fname, content in pages.items():
                with open(os.path.join(output_dir, fname), "w") as f:
                    f.write(content)
            return f"Wiki generated: {len(pages)} pages in {output_dir}"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
