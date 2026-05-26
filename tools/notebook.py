"""Notebook tool — read/write/execute Jupyter .ipynb files."""

import json, os
from pathlib import Path

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "notebook_read",
            "description": "Read a Jupyter notebook (.ipynb) file. Returns all cells with source and outputs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to .ipynb file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebook_edit",
            "description": "Edit a cell in a Jupyter notebook. Replace, insert, or delete cells.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to .ipynb file"},
                    "cell_number": {"type": "integer", "description": "Cell index (0-based)"},
                    "new_source": {"type": "string", "description": "New cell source code"},
                    "cell_type": {"type": "string", "description": "Cell type: code or markdown"},
                    "edit_mode": {"type": "string", "description": "Mode: replace, insert, delete"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notebook_run",
            "description": "Execute a Jupyter notebook cell by cell. Returns outputs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to .ipynb file"},
                    "cell_range": {"type": "string", "description": "Cell range to run: 'all', '0-5', or '3'"}
                },
                "required": ["path"]
            }
        }
    },
]

TOOL_NAMES = {"notebook_read", "notebook_edit", "notebook_run"}

def read(path):
    p = Path(path).expanduser()
    if not p.exists():
        return f"Error: File not found: {path}"
    try:
        nb = json.loads(p.read_text())
        cells = nb.get("cells", [])
        result = [f"Notebook: {p.name} ({len(cells)} cells)"]
        for i, cell in enumerate(cells):
            ctype = cell.get("cell_type", "code")
            src = "".join(cell.get("source", []))
            outputs = cell.get("outputs", [])
            result.append(f"\n--- Cell {i} [{ctype}] ---")
            result.append(src)
            if outputs:
                for out in outputs:
                    if "text" in out:
                        result.append(f"  Output: {''.join(out['text'])[:200]}")
                    elif "data" in out:
                        for mime, data in out["data"].items():
                            if "text" in mime:
                                result.append(f"  Output: {''.join(data)[:200]}")
        return "\n".join(result)
    except Exception as e:
        return f"Error reading notebook: {e}"

def edit(path, cell_number=None, new_source="", cell_type="code", edit_mode="replace"):
    p = Path(path).expanduser()
    if not p.exists():
        return f"Error: File not found: {path}"
    try:
        nb = json.loads(p.read_text())
        cells = nb.get("cells", [])
        if edit_mode == "insert":
            new_cell = {
                "cell_type": cell_type,
                "metadata": {},
                "source": new_source.split("\n") if isinstance(new_source, str) else new_source,
                "outputs": []
            }
            if cell_number is not None and 0 <= cell_number <= len(cells):
                cells.insert(cell_number, new_cell)
            else:
                cells.append(new_cell)
        elif edit_mode == "delete":
            if cell_number is not None and 0 <= cell_number < len(cells):
                cells.pop(cell_number)
            else:
                return f"Error: Invalid cell number {cell_number}"
        else:  # replace
            if cell_number is not None and 0 <= cell_number < len(cells):
                cells[cell_number]["source"] = new_source.split("\n") if isinstance(new_source, str) else new_source
                if cell_type:
                    cells[cell_number]["cell_type"] = cell_type
                cells[cell_number]["outputs"] = []
            else:
                return f"Error: Invalid cell number {cell_number}"
        nb["cells"] = cells
        p.write_text(json.dumps(nb, indent=1))
        return f"Notebook updated: {len(cells)} cells"
    except Exception as e:
        return f"Error editing notebook: {e}"

def run(path, cell_range="all"):
    """Execute notebook cells using Python subprocess. Returns outputs."""
    p = Path(path).expanduser()
    if not p.exists():
        return f"Error: File not found: {path}"
    try:
        nb = json.loads(p.read_text())
        cells = nb.get("cells", [])
        total = len(cells)
        if cell_range == "all":
            start, end = 0, total
        elif "-" in cell_range:
            parts = cell_range.split("-")
            start, end = int(parts[0]), int(parts[1])
        else:
            start = end = int(cell_range) + 1
        results = [f"Notebook: {p.name} | Cells {start}-{end-1} of {total}"]
        for i in range(start, min(end, total)):
            cell = cells[i]
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", []))
            results.append(f"\n[Cell {i}] >>>")
            results.append(src)
            # Execute the cell code
            import subprocess
            try:
                r = subprocess.run(
                    ["python3", "-c", src],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(p.parent)
                )
                if r.stdout:
                    results.append(f"<<< {r.stdout.strip()}")
                if r.stderr:
                    results.append(f"!!! {r.stderr.strip()}")
                if not r.stdout and not r.stderr:
                    results.append("<<< (no output)")
            except subprocess.TimeoutExpired:
                results.append("!!! Timeout (30s)")
            except Exception as e:
                results.append(f"!!! Error: {e}")
        return "\n".join(results)
    except Exception as e:
        return f"Error running notebook: {e}"

def execute(name, args, work_dir=None):
    if name == "notebook_read":
        return read(args.get("path", ""))
    elif name == "notebook_edit":
        return edit(
            args.get("path", ""),
            args.get("cell_number"),
            args.get("new_source", ""),
            args.get("cell_type", "code"),
            args.get("edit_mode", "replace"))
    elif name == "notebook_run":
        return run(args.get("path", ""), args.get("cell_range", "all"))
    return f"Unknown notebook tool: {name}"
