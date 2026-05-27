"""Accurate token counting using tiktoken."""


_tiktoken = None
_encoding = None

def _get_encoding():
    global _tiktoken, _encoding
    if _encoding is None:
        try:
            import tiktoken
            _tiktoken = tiktoken
            _encoding = tiktoken.encoding_for_model("gpt-4")
        except ImportError:
            _encoding = "fallback"
    return _encoding

def count_tokens(text):
    """Count tokens in text. Uses tiktoken if available, falls back to len//4."""
    if not text:
        return 0
    enc = _get_encoding()
    if enc == "fallback":
        return len(text) // 4
    return len(enc.encode(text))

def count_messages_tokens(messages):
    """Count total tokens in a message list."""
    total = 0
    for msg in messages:
        # Overhead per message
        total += 4
        for key, val in msg.items():
            if isinstance(val, str):
                total += count_tokens(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                total += count_tokens(v)
    total += 2  # priming
    return total

def truncate_to_tokens(text, max_tokens):
    """Truncate text to max_tokens."""
    if not text:
        return ""
    enc = _get_encoding()
    if enc == "fallback":
        return text[:max_tokens * 4]
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens])

TOOL_DEFS = []

def execute(name, args, work_dir=None, bot=None):
    return ""
