"""Image tool — read images as base64 for multimodal analysis."""

import base64, os
from pathlib import Path

EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

def read_image(path):
    """Read an image file and return structured data for multimodal API."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"Error: File not found: {path}"
    ext = p.suffix.lower()
    if ext not in EXTS:
        return f"Error: Not an image file: {path} (supported: {', '.join(EXTS)})"
    try:
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
        }.get(ext, "image/png")
        size_kb = len(data) / 1024
        # Return dict for multimodal API content parts
        return {
            "type": "image",
            "mime": mime,
            "base64": b64,
            "filename": p.name,
            "size_kb": round(size_kb, 1),
        }
    except Exception as e:
        return f"Error reading image: {e}"

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "read_image",
            "description": "Read an image file (PNG, JPG, GIF, WebP, BMP, SVG). Returns base64-encoded data for multimodal analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the image file"}
                },
                "required": ["path"]
            }
        }
    }
]

TOOL_NAMES = {"read_image"}

def execute(name, args, work_dir=None):
    if name == "read_image":
        return read_image(args.get("path", ""))
    return f"Unknown image tool: {name}"
