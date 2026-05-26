"""Text processing, regex, encoding, and hashing tools."""

import re, hashlib, base64, os, difflib, urllib.parse, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "regex_match", "description": "Test a regex pattern against text. Returns all matches with groups.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern"}, "text": {"type": "string", "description": "Text to match against"}, "flags": {"type": "string", "description": "Flags: 'i' for case-insensitive, 'm' for multiline, 's' for dotall"}}, "required": ["pattern", "text"]}}},
    {"type": "function", "function": {"name": "regex_replace", "description": "Find and replace using regex pattern in text.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string", "description": "Regex pattern to find"}, "replacement": {"type": "string", "description": "Replacement string (supports \\1, \\2 backrefs)"}, "text": {"type": "string", "description": "Input text"}}, "required": ["pattern", "replacement", "text"]}}},
    {"type": "function", "function": {"name": "text_replace_bulk", "description": "Bulk find-and-replace across multiple files in a directory.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory or file path"}, "find": {"type": "string", "description": "Text to find"}, "replace": {"type": "string", "description": "Replacement text"}, "include": {"type": "string", "description": "File glob filter (e.g. '*.py')"}}, "required": ["path", "find", "replace"]}}},
    {"type": "function", "function": {"name": "text_diff", "description": "Compare two texts and show differences.", "parameters": {"type": "object", "properties": {"text1": {"type": "string", "description": "First text"}, "text2": {"type": "string", "description": "Second text"}, "context": {"type": "integer", "description": "Context lines (default 3)"}}, "required": ["text1", "text2"]}}},
    {"type": "function", "function": {"name": "text_count", "description": "Count words, lines, characters, and sentences in text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Input text"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "text_extract", "description": "Extract patterns (emails, URLs, IPs, phone numbers) from text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Input text"}, "type": {"type": "string", "enum": ["emails", "urls", "ips", "phones", "dates", "hashtags", "mentions", "all"], "description": "Type to extract (default 'all')"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "text_transform", "description": "Transform text case: upper, lower, title, camel, snake, kebab, reverse.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Input text"}, "transform": {"type": "string", "enum": ["upper", "lower", "title", "camel", "snake", "kebab", "reverse", "capitalize", "swapcase"], "description": "Transform type"}}, "required": ["text", "transform"]}}},
    {"type": "function", "function": {"name": "text_wrap", "description": "Wrap text to specified line width.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Input text"}, "width": {"type": "integer", "description": "Max line width (default 80)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "text_join", "description": "Join multiple strings with a separator.", "parameters": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}, "description": "Strings to join"}, "separator": {"type": "string", "description": "Separator (default newline)"}}, "required": ["items"]}}},
    {"type": "function", "function": {"name": "text_sort", "description": "Sort lines in text alphabetically or numerically.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text with lines to sort"}, "reverse": {"type": "boolean", "description": "Sort in reverse order (default false)"}, "numeric": {"type": "boolean", "description": "Numeric sort (default false)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "text_dedup", "description": "Remove duplicate lines from text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Input text"}, "keep_order": {"type": "boolean", "description": "Preserve original order (default true)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "base64_encode", "description": "Encode text or file to Base64.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to encode"}, "file": {"type": "string", "description": "File path to encode (alternative to text)"}}, "required": []}}},
    {"type": "function", "function": {"name": "base64_decode", "description": "Decode Base64 to text.", "parameters": {"type": "object", "properties": {"encoded": {"type": "string", "description": "Base64 string to decode"}}, "required": ["encoded"]}}},
    {"type": "function", "function": {"name": "hash_generate", "description": "Generate hash of text or file. Supports MD5, SHA1, SHA256, SHA512.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to hash"}, "file": {"type": "string", "description": "File to hash (alternative to text)"}, "algorithm": {"type": "string", "enum": ["md5", "sha1", "sha256", "sha512"], "description": "Hash algorithm (default sha256)"}}, "required": []}}},
    {"type": "function", "function": {"name": "url_encode", "description": "URL-encode a string.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to encode"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "url_decode", "description": "URL-decode a string.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to decode"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "html_encode", "description": "HTML-encode special characters.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to encode"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "html_decode", "description": "Decode HTML entities.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "HTML text to decode"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "jwt_decode", "description": "Decode a JWT token (without verification). Shows header and payload.", "parameters": {"type": "object", "properties": {"token": {"type": "string", "description": "JWT token string"}}, "required": ["token"]}}},
    {"type": "function", "function": {"name": "uuid_generate", "description": "Generate a UUID (v4 random).", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "description": "Number of UUIDs to generate (default 1)"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "regex_match":
            flags = 0
            for c in args.get("flags", ""):
                if c == "i": flags |= re.IGNORECASE
                if c == "m": flags |= re.MULTILINE
                if c == "s": flags |= re.DOTALL
            matches = list(re.finditer(args["pattern"], args["text"], flags))
            if not matches:
                return "(no matches)"
            lines = []
            for m in matches[:50]:
                lines.append(f"Match: '{m.group()}' at pos {m.start()}-{m.end()}")
                for i, g in enumerate(m.groups(), 1):
                    lines.append(f"  Group {i}: '{g}'")
            return "\n".join(lines)

        elif name == "regex_replace":
            result = re.sub(args["pattern"], args["replacement"], args["text"])
            return result[:5000]

        elif name == "text_replace_bulk":
            path = args["path"]
            find = args["find"]
            replace = args["replace"]
            include = args.get("include", "")
            count = 0
            files = []
            if os.path.isfile(path):
                targets = [path]
            else:
                targets = []
                for root, dirs, fnames in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'}]
                    for fn in fnames:
                        if include and not fn.endswith(include.lstrip("*")):
                            continue
                        targets.append(os.path.join(root, fn))
            for fp in targets[:500]:
                try:
                    with open(fp) as f:
                        content = f.read()
                    if find in content:
                        new_content = content.replace(find, replace)
                        with open(fp, "w") as f:
                            f.write(new_content)
                        n = content.count(find)
                        count += n
                        files.append(f"{fp} ({n} replacements)")
                except:
                    continue
            return f"Replaced {count} occurrences in {len(files)} files:\n" + "\n".join(files[:50])

        elif name == "text_diff":
            t1 = args["text1"].splitlines(keepends=True)
            t2 = args["text2"].splitlines(keepends=True)
            diff = list(difflib.unified_diff(t1, t2, fromfile="text1", tofile="text2", n=args.get("context", 3)))
            return "".join(diff)[:5000] or "(texts are identical)"

        elif name == "text_count":
            text = args["text"]
            words = len(text.split())
            lines = text.count("\n") + 1
            chars = len(text)
            sentences = len(re.findall(r'[.!?]+', text))
            return f"Words: {words}\nLines: {lines}\nCharacters: {chars}\nSentences: {sentences}"

        elif name == "text_extract":
            text = args["text"]
            etype = args.get("type", "all")
            results = {}
            patterns = {
                "emails": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                "urls": r'https?://[^\s<>"{}|\\^`\[\]]+',
                "ips": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                "phones": r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}',
                "dates": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                "hashtags": r'#\w+',
                "mentions": r'@\w+',
            }
            if etype == "all":
                for t, p in patterns.items():
                    results[t] = list(set(re.findall(p, text)))
            else:
                results[etype] = list(set(re.findall(patterns.get(etype, ""), text)))
            lines = []
            for t, matches in results.items():
                lines.append(f"{t}: {', '.join(matches[:20])}" if matches else f"{t}: (none)")
            return "\n".join(lines)

        elif name == "text_transform":
            text = args["text"]
            t = args["transform"]
            if t == "upper": return text.upper()
            if t == "lower": return text.lower()
            if t == "title": return text.title()
            if t == "capitalize": return text.capitalize()
            if t == "swapcase": return text.swapcase()
            if t == "reverse": return text[::-1]
            if t == "snake":
                s = re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
                return s.replace("-", "_").replace(" ", "_")
            if t == "kebab":
                s = re.sub(r'(?<!^)(?=[A-Z])', '-', text).lower()
                return s.replace("_", "-").replace(" ", "-")
            if t == "camel":
                parts = re.split(r'[-_\s]+', text)
                return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
            return text

        elif name == "text_wrap":
            import textwrap
            return "\n".join(textwrap.wrap(args["text"], args.get("width", 80)))

        elif name == "text_join":
            sep = args.get("separator", "\n")
            return sep.join(args["items"])

        elif name == "text_sort":
            lines = args["text"].splitlines()
            reverse = args.get("reverse", False)
            if args.get("numeric"):
                lines.sort(key=lambda x: float(re.search(r'-?\d+', x).group()) if re.search(r'-?\d+', x) else 0, reverse=reverse)
            else:
                lines.sort(reverse=reverse)
            return "\n".join(lines)

        elif name == "text_dedup":
            lines = args["text"].splitlines()
            if args.get("keep_order", True):
                seen = set()
                result = []
                for l in lines:
                    if l not in seen:
                        seen.add(l)
                        result.append(l)
                return "\n".join(result)
            return "\n".join(sorted(set(lines)))

        elif name == "base64_encode":
            if args.get("file"):
                with open(args["file"], "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return base64.b64encode(args["text"].encode()).decode()

        elif name == "base64_decode":
            return base64.b64decode(args["encoded"]).decode(errors="replace")

        elif name == "hash_generate":
            algo = args.get("algorithm", "sha256")
            h = hashlib.new(algo)
            if args.get("file"):
                with open(args["file"], "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        h.update(chunk)
            else:
                h.update(args.get("text", "").encode())
            return f"{algo}: {h.hexdigest()}"

        elif name == "url_encode":
            return urllib.parse.quote(args["text"], safe="")

        elif name == "url_decode":
            return urllib.parse.unquote(args["text"])

        elif name == "html_encode":
            return args["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

        elif name == "html_decode":
            import html
            return html.unescape(args["text"])

        elif name == "jwt_decode":
            parts = args["token"].split(".")
            if len(parts) != 3:
                return "Error: Invalid JWT format"
            header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
            return f"Header:\n{json.dumps(header, indent=2)}\n\nPayload:\n{json.dumps(payload, indent=2)}"

        elif name == "uuid_generate":
            import uuid
            count = args.get("count", 1)
            return "\n".join(str(uuid.uuid4()) for _ in range(count))

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
