"""Memory system — persistent context across sessions."""

import os, re, time
from pathlib import Path

DIR = Path(__file__).parent.parent / "memory"
INDEX = DIR / "MEMORY.md"

# ─── Memory Types ─────────────────────────────────────────────────────────────
TYPES = ("user", "feedback", "project", "reference")

# ─── Core Operations ──────────────────────────────────────────────────────────
def init():
    """Ensure memory directories exist."""
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "team").mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text("# Memory\n\n")

def save(name, content, mtype="project", scope="private"):
    """Save a memory to file and update index."""
    init()
    safe_name = re.sub(r'[^a-z0-9\-]', '-', name.lower().strip())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')
    if not safe_name:
        safe_name = f"memory-{int(time.time())}"

    target_dir = DIR / "team" if scope == "team" else DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    fpath = target_dir / f"{safe_name}.md"

    # Write memory file with frontmatter
    desc = content.split('\n')[0][:120] if content else name
    frontmatter = f"""---
name: {name}
description: {desc}
type: {mtype}
scope: {scope}
---

{content}
"""
    fpath.write_text(frontmatter)

    # Update index
    _update_index(target_dir, safe_name, desc)
    return fpath

def _update_index(target_dir, safe_name, desc):
    """Add entry to MEMORY.md index if not already present."""
    idx = target_dir / "MEMORY.md"
    if not idx.exists():
        idx.write_text("# Memory\n\n")

    text = idx.read_text()
    link = f"[{safe_name}]({safe_name}.md)"
    if link not in text:
        entry = f"- {link} — {desc}\n"
        with open(idx, "a") as f:
            f.write(entry)

def load(name):
    """Load a memory by name."""
    safe_name = re.sub(r'[^a-z0-9\-]', '-', name.lower().strip())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')

    for search_dir in [DIR, DIR / "team"]:
        fpath = search_dir / f"{safe_name}.md"
        if fpath.exists():
            text = fpath.read_text()
            # Strip frontmatter
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
            return text
    return None

def list_memories(scope=None):
    """List all memories."""
    init()
    results = []
    search_dirs = []
    if scope == "team":
        search_dirs = [DIR / "team"]
    elif scope == "private":
        search_dirs = [DIR]
    else:
        search_dirs = [DIR, DIR / "team"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in sorted(search_dir.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            text = f.read_text()
            name = f.stem
            desc = ""
            mtype = "project"
            scope_val = "private" if search_dir == DIR else "team"

            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    meta = parts[1]
                    for line in meta.strip().split("\n"):
                        if line.startswith("name:"):
                            name = line[5:].strip()
                        elif line.startswith("description:"):
                            desc = line[12:].strip()
                        elif line.startswith("type:"):
                            mtype = line[5:].strip()
                        elif line.startswith("scope:"):
                            scope_val = line[6:].strip()

            results.append({
                "name": name,
                "file": str(f),
                "description": desc,
                "type": mtype,
                "scope": scope_val,
            })
    return results

def search(query):
    """Search memory content for a term."""
    init()
    results = []
    query_lower = query.lower()
    for search_dir in [DIR, DIR / "team"]:
        if not search_dir.exists():
            continue
        for f in search_dir.glob("*.md"):
            if f.name == "MEMORY.md":
                continue
            text = f.read_text()
            if query_lower in text.lower():
                name = f.stem
                desc = ""
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].strip().split("\n"):
                            if line.startswith("name:"):
                                name = line[5:].strip()
                            elif line.startswith("description:"):
                                desc = line[12:].strip()
                results.append({"name": name, "file": str(f), "description": desc})
    return results

def delete(name):
    """Delete a memory by name."""
    safe_name = re.sub(r'[^a-z0-9\-]', '-', name.lower().strip())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')

    for search_dir in [DIR, DIR / "team"]:
        fpath = search_dir / f"{safe_name}.md"
        if fpath.exists():
            fpath.unlink()
            # Remove from index
            idx = search_dir / "MEMORY.md"
            if idx.exists():
                text = idx.read_text()
                link = f"[{safe_name}]({safe_name}.md)"
                lines = text.split("\n")
                new_lines = [l for l in lines if link not in l]
                idx.write_text("\n".join(new_lines))
            return True
    return False
