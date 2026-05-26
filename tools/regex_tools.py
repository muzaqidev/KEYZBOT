"""Advanced regex and pattern tools."""

import re, os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "regex_test", "description": "Test a regex pattern and show all matches with group details.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern"}, "text": {"type": "string", "description": "Text to test against"}, "flags": {"type": "string", "description": "Flags: i=ignorecase, m=multiline, s=dotall, x=verbose"}}, "required": ["pattern", "text"]}}},
    {"type": "function", "function": {"name": "regex_build", "description": "Build a regex pattern from a natural language description.", "parameters": {"type": "object", "properties": {"description": {"type": "string", "description": "What to match (e.g. 'email address', 'IPv4 address', 'URL')"}}, "required": ["description"]}}},
    {"type": "function", "function": {"name": "regex_explain", "description": "Explain what a regex pattern does in plain English.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern to explain"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "pattern_find_files", "description": "Find files matching a naming pattern/regex across directories.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory to search"}, "pattern": {"type": "string", "description": "Regex pattern for filename"}, "recursive": {"type": "boolean", "description": "Search recursively (default true)"}}, "required": ["path", "pattern"]}}},
    {"type": "function", "function": {"name": "pattern_count", "description": "Count occurrences of a pattern in each file.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory"}, "pattern": {"type": "string", "description": "Regex pattern"}, "include": {"type": "string", "description": "File glob filter"}}, "required": ["path", "pattern"]}}},
    {"type": "function", "function": {"name": "log_parse", "description": "Parse log files and extract structured data using regex patterns.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Log file path"}, "pattern": {"type": "string", "description": "Regex with named groups (e.g. '(?P<time>\\S+) (?P<level>\\S+) (?P<msg>.*)')"}, "tail": {"type": "integer", "description": "Last N lines (default 100)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "csv_parse_regex", "description": "Parse CSV-like data using regex (for non-standard formats).", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "CSV-like text"}, "delimiter": {"type": "string", "description": "Column delimiter (default comma)"}, "quote": {"type": "string", "description": "Quote character (default double-quote)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "ansi_strip", "description": "Strip ANSI escape codes from text (terminal color codes).", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text with ANSI codes"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "html_strip", "description": "Strip HTML tags from text, leaving plain text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "HTML text"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "markdown_parse", "description": "Parse markdown and extract structure: headings, links, code blocks, images.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Markdown text"}}, "required": ["text"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "regex_test":
            flags = 0
            for c in args.get("flags", ""):
                if c == "i": flags |= re.IGNORECASE
                if c == "m": flags |= re.MULTILINE
                if c == "s": flags |= re.DOTALL
                if c == "x": flags |= re.VERBOSE
            matches = list(re.finditer(args["pattern"], args["text"], flags))
            if not matches:
                return "No matches found"
            lines = []
            for i, m in enumerate(matches[:30], 1):
                lines.append(f"Match {i}: '{m.group()}' at [{m.start()}:{m.end()}]")
                for gi, g in enumerate(m.groups(), 1):
                    lines.append(f"  Group {gi}: '{g}'")
                for k, v in (m.groupdict() or {}).items():
                    lines.append(f"  Named '{k}': '{v}'")
            return "\n".join(lines)

        elif name == "regex_build":
            desc = args["description"].lower()
            patterns = {
                "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                "url": r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                "ipv4": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                "ipv6": r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}',
                "phone": r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}',
                "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                "time": r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?\b',
                "hex color": r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b',
                "html tag": r'<[^>]+>',
                "uuid": r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                "credit card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                "mac address": r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}',
                "domain": r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
                "hashtag": r'#\w+',
                "mention": r'@\w+',
            }
            for key, pat in patterns.items():
                if key in desc:
                    return f"Pattern: {pat}\nDescription: matches {key}"
            return f"No built-in pattern for '{desc}'. Try: email, url, ipv4, phone, date, uuid, html tag, etc."

        elif name == "regex_explain":
            pattern = args["pattern"]
            parts = []
            i = 0
            while i < len(pattern):
                c = pattern[i]
                if c == '\\':
                    nxt = pattern[i+1] if i+1 < len(pattern) else ''
                    escapes = {'d': 'digit', 'w': 'word char', 's': 'whitespace', 'b': 'word boundary', 'D': 'non-digit', 'W': 'non-word', 'S': 'non-whitespace', 'n': 'newline', 't': 'tab'}
                    parts.append(f"\\{nxt} = {escapes.get(nxt, 'literal ' + nxt)}")
                    i += 2
                elif c == '[':
                    end = pattern.index(']', i)
                    parts.append(f"[{pattern[i+1:end]}] = character class")
                    i = end + 1
                elif c == '(':
                    parts.append("( = group start")
                    i += 1
                elif c == ')':
                    parts.append(") = group end")
                    i += 1
                elif c == '{':
                    end = pattern.index('}', i)
                    parts.append(f"{pattern[i:end+1]} = quantifier")
                    i = end + 1
                elif c == '*': parts.append("* = 0 or more"); i += 1
                elif c == '+': parts.append("+ = 1 or more"); i += 1
                elif c == '?': parts.append("? = 0 or 1 (optional)"); i += 1
                elif c == '.': parts.append(". = any character"); i += 1
                elif c == '^': parts.append("^ = start of string/line"); i += 1
                elif c == '$': parts.append("$ = end of string/line"); i += 1
                elif c == '|': parts.append("| = OR"); i += 1
                else: parts.append(f"'{c}' = literal"); i += 1
            return "\n".join(parts[:50])

        elif name == "pattern_find_files":
            path = args.get("path", ".")
            pattern = args["pattern"]
            recursive = args.get("recursive", True)
            matches = []
            if recursive:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
                    for f in files:
                        if re.search(pattern, f):
                            matches.append(os.path.join(root, f))
            else:
                try:
                    for f in os.listdir(path):
                        if re.search(pattern, f):
                            matches.append(os.path.join(path, f))
                except:
                    pass
            return "\n".join(matches[:100]) or "(no matches)"

        elif name == "pattern_count":
            path = args["path"]
            pattern = args["pattern"]
            include = args.get("include", "")
            results = []
            targets = [path] if os.path.isfile(path) else []
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules'}]
                    for f in files:
                        if include and not f.endswith(include.lstrip("*")):
                            continue
                        targets.append(os.path.join(root, f))
            for fp in targets[:200]:
                try:
                    with open(fp) as f:
                        content = f.read()
                    count = len(re.findall(pattern, content))
                    if count:
                        results.append(f"{fp}: {count}")
                except:
                    continue
            return "\n".join(results) or "(no matches)"

        elif name == "log_parse":
            path = args["path"]
            pattern = args.get("pattern", r'(?P<time>\S+)\s+(?P<level>\S+)\s+(?P<msg>.*)')
            tail = args.get("tail", 100)
            with open(path) as f:
                lines = f.readlines()[-tail:]
            results = []
            for line in lines:
                m = re.search(pattern, line.strip())
                if m:
                    results.append(json.dumps(m.groupdict(), ensure_ascii=False))
            return "\n".join(results[:50]) or "(no matching entries)"

        elif name == "csv_parse_regex":
            text = args["text"]
            delimiter = args.get("delimiter", ",")
            quote = args.get("quote", '"')
            lines = text.strip().split("\n")
            results = []
            for line in lines:
                if not line.strip():
                    continue
                # Handle quoted fields
                fields = []
                field = ""
                in_quote = False
                for c in line:
                    if c == quote:
                        in_quote = not in_quote
                    elif c == delimiter and not in_quote:
                        fields.append(field.strip())
                        field = ""
                    else:
                        field += c
                fields.append(field.strip())
                results.append(fields)
            return json.dumps(results, indent=2, ensure_ascii=False)[:5000]

        elif name == "ansi_strip":
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', args["text"])

        elif name == "html_strip":
            text = args["text"]
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()[:5000]

        elif name == "markdown_parse":
            text = args["text"]
            headings = re.findall(r'^(#{1,6})\s+(.+)', text, re.MULTILINE)
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
            code_blocks = re.findall(r'```(\w*)\n(.*?)```', text, re.DOTALL)
            images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
            lines = []
            if headings:
                lines.append("Headings:")
                for h in headings:
                    lines.append(f"  {'  ' * (len(h[0])-1)}{h[1]}")
            if links:
                lines.append(f"\nLinks ({len(links)}):")
                for t, u in links[:20]:
                    lines.append(f"  {t} -> {u}")
            if code_blocks:
                lines.append(f"\nCode blocks ({len(code_blocks)}):")
                for lang, _ in code_blocks:
                    lines.append(f"  [{lang or 'plain'}]")
            if images:
                lines.append(f"\nImages ({len(images)}):")
                for alt, src in images[:10]:
                    lines.append(f"  {alt} -> {src}")
            return "\n".join(lines) or "(no structure found)"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
