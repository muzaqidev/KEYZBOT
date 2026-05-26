"""AI and LLM utility tools — summarization, translation, analysis via local/provider APIs."""

import os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "text_summarize", "description": "Summarize a long text into key points.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to summarize"}, "max_sentences": {"type": "integer", "description": "Max sentences in summary (default 5)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "text_translate", "description": "Translate text between languages using AI.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to translate"}, "target_lang": {"type": "string", "description": "Target language (e.g. 'en', 'id', 'ja', 'zh')"}, "source_lang": {"type": "string", "description": "Source language (auto-detected if omitted)"}}, "required": ["text", "target_lang"]}}},
    {"type": "function", "function": {"name": "sentiment_analyze", "description": "Analyze sentiment of text: positive, negative, or neutral with confidence score.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to analyze"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "entity_extract", "description": "Extract named entities: people, organizations, locations, dates, etc.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to analyze"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "keyword_extract", "description": "Extract key topics and keywords from text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to analyze"}, "count": {"type": "integer", "description": "Number of keywords (default 10)"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "language_detect", "description": "Detect the language of a text.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to analyze"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "code_explain", "description": "Explain what a piece of code does in plain English.", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Code to explain"}, "language": {"type": "string", "description": "Programming language (auto-detected)"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "code_review", "description": "Review code for bugs, performance issues, and best practices.", "parameters": {"type": "object", "properties": {"code": {"type": "string", "description": "Code to review"}, "language": {"type": "string", "description": "Programming language"}}, "required": ["code"]}}},
    {"type": "function", "function": {"name": "text_classify", "description": "Classify text into provided categories.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to classify"}, "categories": {"type": "array", "items": {"type": "string"}, "description": "Categories to classify into"}}, "required": ["text", "categories"]}}},
    {"type": "function", "function": {"name": "readme_generate", "description": "Generate a README.md for a project based on its structure and code.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Project directory path"}, "style": {"type": "string", "enum": ["minimal", "standard", "detailed"], "description": "README style (default standard)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "changelog_generate", "description": "Generate a changelog from git commit history.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Git repository path"}, "since": {"type": "string", "description": "Since commit/tag (default: last 20 commits)"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "docstring_generate", "description": "Generate docstrings for Python functions.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Python file path"}, "style": {"type": "string", "enum": ["google", "numpy", "sphinx"], "description": "Docstring style (default google)"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def _get_provider():
    """Get active AI provider config for making API calls."""
    try:
        from core import config
        cfg = config.get_active_config() or config.DEFAULTS
        return {
            "base_url": cfg.get("base_url", ""),
            "api_key": cfg.get("api_key", ""),
            "model": cfg.get("model", ""),
        }
    except:
        return None


def _ai_call(prompt, max_tokens=500):
    """Make a quick AI API call."""
    import requests
    provider = _get_provider()
    if not provider or not provider["base_url"]:
        return None
    headers = {"Content-Type": "application/json"}
    if provider["api_key"]:
        headers["Authorization"] = f"Bearer {provider['api_key']}"
    payload = {
        "model": provider["model"],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        resp = requests.post(f"{provider['base_url']}/chat/completions", headers=headers, json=payload, timeout=30)
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def execute(name, args, work_dir=None):
    try:
        if name == "text_summarize":
            text = args["text"][:3000]
            max_s = args.get("max_sentences", 5)
            prompt = f"Summarize this text in {max_s} key sentences:\n\n{text}"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "text_translate":
            text = args["text"][:2000]
            target = args["target_lang"]
            source = args.get("source_lang", "auto")
            prompt = f"Translate the following {source} text to {target}. Return only the translation:\n\n{text}"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "sentiment_analyze":
            text = args["text"][:1000]
            prompt = f"Analyze the sentiment of this text. Return: sentiment (positive/negative/neutral), confidence (0-1), and brief explanation:\n\n{text}"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "entity_extract":
            text = args["text"][:2000]
            prompt = f"Extract all named entities from this text. Group by type (Person, Organization, Location, Date, etc.):\n\n{text}"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "keyword_extract":
            text = args["text"][:2000]
            count = args.get("count", 10)
            prompt = f"Extract the top {count} keywords/topics from this text. Return as a comma-separated list:\n\n{text}"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "language_detect":
            text = args["text"][:500]
            prompt = f"What language is this text written in? Return only the language name:\n\n{text}"
            result = _ai_call(prompt, max_tokens=50)
            return result or "Error: Could not connect to AI provider"

        elif name == "code_explain":
            code = args["code"][:3000]
            lang = args.get("language", "")
            prompt = f"Explain what this {lang} code does in plain English. Be concise:\n\n```\n{code}\n```"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "code_review":
            code = args["code"][:3000]
            lang = args.get("language", "")
            prompt = f"Review this {lang} code for bugs, security issues, performance problems, and best practices. Be specific:\n\n```\n{code}\n```"
            result = _ai_call(prompt)
            return result or "Error: Could not connect to AI provider"

        elif name == "text_classify":
            text = args["text"][:1000]
            cats = ", ".join(args["categories"])
            prompt = f"Classify this text into one of these categories: [{cats}]. Return the category and confidence:\n\n{text}"
            result = _ai_call(prompt, max_tokens=200)
            return result or "Error: Could not connect to AI provider"

        elif name == "readme_generate":
            path = args.get("path", ".")
            style = args.get("style", "standard")
            # Gather project info
            info_lines = []
            for f in ["package.json", "requirements.txt", "Cargo.toml", "go.mod"]:
                fp = os.path.join(path, f)
                if os.path.exists(fp):
                    with open(fp) as fh:
                        info_lines.append(f"[{f}]\n{fh.read()[:500]}")
            # List top-level files
            try:
                files = os.listdir(path)[:30]
                info_lines.append(f"Files: {', '.join(files)}")
            except:
                pass
            prompt = f"Generate a {style} README.md for this project:\n\n" + "\n\n".join(info_lines)
            result = _ai_call(prompt, max_tokens=1000)
            return result or "Error: Could not connect to AI provider"

        elif name == "changelog_generate":
            import subprocess
            path = args.get("path", ".")
            since = args.get("since", "")
            cmd = ["git", "log", "--oneline", "--no-merges"]
            if since:
                cmd.append(f"{since}..HEAD")
            else:
                cmd = cmd[:2] + ["-20"] + cmd[2:]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=path)
            commits = r.stdout.strip()
            if not commits:
                return "No commits found"
            prompt = f"Generate a changelog from these commits. Group by type (Features, Fixes, Improvements):\n\n{commits}"
            result = _ai_call(prompt, max_tokens=1000)
            return result or f"Commits:\n{commits}"

        elif name == "docstring_generate":
            path = args["path"]
            style = args.get("style", "google")
            with open(path) as f:
                content = f.read()[:5000]
            prompt = f"Add {style}-style docstrings to all functions in this Python file. Return the complete file with docstrings added:\n\n```python\n{content}\n```"
            result = _ai_call(prompt, max_tokens=2000)
            return result or "Error: Could not connect to AI provider"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
