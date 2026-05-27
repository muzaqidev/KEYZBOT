"""Clipboard and quick-access tools — copy, paste, snippets, history."""

import os, json, time

TOOL_DEFS = [
    {"type": "function", "function": {"name": "clipboard_set", "description": "Copy text to system clipboard.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to copy"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "clipboard_get", "description": "Get current clipboard content.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "snippet_save", "description": "Save a code snippet for later reuse.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Snippet name/identifier"}, "code": {"type": "string", "description": "Code content"}, "language": {"type": "string", "description": "Language (e.g. python, js, bash)"}}, "required": ["name", "code"]}}},
    {"type": "function", "function": {"name": "snippet_load", "description": "Load a saved code snippet by name.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Snippet name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "snippet_list", "description": "List all saved code snippets.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "snippet_delete", "description": "Delete a saved code snippet.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Snippet name"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "bookmark_save", "description": "Save a URL bookmark with title and tags.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to bookmark"}, "title": {"type": "string", "description": "Bookmark title"}, "tags": {"type": "string", "description": "Comma-separated tags"}}, "required": ["url", "title"]}}},
    {"type": "function", "function": {"name": "bookmark_list", "description": "List saved bookmarks, optionally filtered by tag.", "parameters": {"type": "object", "properties": {"tag": {"type": "string", "description": "Filter by tag"}}, "required": []}}},
    {"type": "function", "function": {"name": "bookmark_delete", "description": "Delete a saved bookmark.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to delete"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "note_save", "description": "Save a quick note with optional category.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Note content"}, "category": {"type": "string", "description": "Category (default: general)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "note_list", "description": "List saved notes, optionally filtered by category.", "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "Filter by category"}, "limit": {"type": "integer", "description": "Max notes (default 20)"}}, "required": []}}},
    {"type": "function", "function": {"name": "note_search", "description": "Search notes by keyword.", "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Search keyword"}}, "required": ["query"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]

_DATA_DIR = os.path.join(os.path.expanduser("~"), ".keyzbot")
_SNIPPETS_FILE = os.path.join(_DATA_DIR, "snippets.json")
_BOOKMARKS_FILE = os.path.join(_DATA_DIR, "bookmarks.json")
_NOTES_FILE = os.path.join(_DATA_DIR, "notes.json")


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save_json(path, data):
    _ensure_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def execute(name, args, work_dir=None):
    try:
        if name == "clipboard_set":
            text = args["text"]
            # Try xclip, xsel, termux-clipboard-set, pbcopy
            for cmd in [["termux-clipboard-set"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"], ["pbcopy"]]:
                try:
                    import subprocess
                    r = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=5)
                    if r.returncode == 0:
                        return "Copied to clipboard"
                except:
                    continue
            # Fallback: save to file
            _ensure_dir()
            with open(os.path.join(_DATA_DIR, "clipboard.txt"), "w") as f:
                f.write(text)
            return "Saved to ~/.keyzbot/clipboard.txt (no clipboard tool available)"

        elif name == "clipboard_get":
            import subprocess
            for cmd in [["termux-clipboard-get"], ["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"], ["pbpaste"]]:
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if r.returncode == 0 and r.stdout.strip():
                        return r.stdout
                except:
                    continue
            # Fallback: read from file
            clip_file = os.path.join(_DATA_DIR, "clipboard.txt")
            if os.path.exists(clip_file):
                with open(clip_file) as f:
                    return f.read()
            return "(clipboard empty or not available)"

        elif name == "snippet_save":
            snippets = _load_json(_SNIPPETS_FILE)
            snippets[args["name"]] = {"code": args["code"], "language": args.get("language", ""), "saved": time.strftime("%Y-%m-%d %H:%M")}
            _save_json(_SNIPPETS_FILE, snippets)
            return f"Snippet '{args['name']}' saved"

        elif name == "snippet_load":
            snippets = _load_json(_SNIPPETS_FILE)
            snip = snippets.get(args["name"])
            if snip:
                return f"[{snip.get('language', '')}]\n{snip['code']}"
            return f"Snippet '{args['name']}' not found"

        elif name == "snippet_list":
            snippets = _load_json(_SNIPPETS_FILE)
            if not snippets:
                return "(no snippets saved)"
            lines = []
            for k, v in snippets.items():
                lines.append(f"  {k} [{v.get('language', '')}] ({v.get('saved', '')})")
            return "\n".join(lines)

        elif name == "snippet_delete":
            snippets = _load_json(_SNIPPETS_FILE)
            if args["name"] in snippets:
                del snippets[args["name"]]
                _save_json(_SNIPPETS_FILE, snippets)
                return f"Deleted snippet '{args['name']}'"
            return f"Snippet '{args['name']}' not found"

        elif name == "bookmark_save":
            bookmarks = _load_json(_BOOKMARKS_FILE)
            bookmarks[args["url"]] = {"title": args["title"], "tags": args.get("tags", ""), "saved": time.strftime("%Y-%m-%d %H:%M")}
            _save_json(_BOOKMARKS_FILE, bookmarks)
            return f"Bookmarked: {args['title']}"

        elif name == "bookmark_list":
            bookmarks = _load_json(_BOOKMARKS_FILE)
            tag = args.get("tag", "")
            if not bookmarks:
                return "(no bookmarks)"
            lines = []
            for url, info in bookmarks.items():
                if tag and tag.lower() not in info.get("tags", "").lower():
                    continue
                lines.append(f"  [{info.get('tags', '')}] {info['title']} — {url}")
            return "\n".join(lines) or "(no matching bookmarks)"

        elif name == "bookmark_delete":
            bookmarks = _load_json(_BOOKMARKS_FILE)
            if args["url"] in bookmarks:
                del bookmarks[args["url"]]
                _save_json(_BOOKMARKS_FILE, bookmarks)
                return "Deleted bookmark"
            return "Bookmark not found"

        elif name == "note_save":
            notes = _load_json(_NOTES_FILE)
            if "items" not in notes:
                notes["items"] = []
            notes["items"].append({
                "text": args["text"],
                "category": args.get("category", "general"),
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            _save_json(_NOTES_FILE, notes)
            return "Note saved"

        elif name == "note_list":
            notes = _load_json(_NOTES_FILE)
            items = notes.get("items", [])
            cat = args.get("category", "")
            limit = args.get("limit", 20)
            if cat:
                items = [n for n in items if n.get("category", "") == cat]
            items = items[-limit:]
            if not items:
                return "(no notes)"
            lines = []
            for n in items:
                lines.append(f"[{n.get('category', '')}] {n.get('time', '')} — {n['text'][:100]}")
            return "\n".join(lines)

        elif name == "note_search":
            notes = _load_json(_NOTES_FILE)
            query = args["query"].lower()
            matches = [n for n in notes.get("items", []) if query in n.get("text", "").lower()]
            if not matches:
                return "(no matching notes)"
            lines = []
            for n in matches[-20:]:
                lines.append(f"[{n.get('category', '')}] {n.get('time', '')} — {n['text'][:100]}")
            return "\n".join(lines)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
