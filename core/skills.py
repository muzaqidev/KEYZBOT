"""Skills system — custom slash commands."""

import json
from pathlib import Path

# Built-in skills (like OpenClaude)
BUILTIN_SKILLS = {
    "commit": {
        "description": "Create a git commit with AI-generated message",
        "prompt": """Analyze the current git changes and create a commit:
1. Run git status and git diff to understand changes
2. Run git log for recent commit style
3. Draft a concise commit message (1-2 sentences, focus on 'why')
4. Stage relevant files and commit
5. Report the result""",
    },
    "review-pr": {
        "description": "Review a pull request",
        "prompt": """Review the current PR:
1. Check git status and diff for uncommitted changes
2. Analyze code quality, potential bugs, security issues
3. Suggest improvements
4. Report findings in a structured format""",
    },
    "simplify": {
        "description": "Review changed code for reuse, quality, efficiency",
        "prompt": """Review the recently changed code:
1. Find recently modified files via git diff
2. Check for code reuse opportunities
3. Check for quality and efficiency issues
4. Fix any issues found
5. Report what was improved""",
    },
    "loop": {
        "description": "Run a prompt on a fixed interval",
        "prompt": "LOOP:{interval}:{prompt}",
    },
    "update-config": {
        "description": "Configure KEYZBOT settings via settings.json",
        "prompt": "Update the KEYZBOT configuration in settings.json based on user request.",
    },
}

# Custom skills loaded from config
_custom_skills = {}

def load_custom():
    """Load custom skills from skills directory."""
    global _custom_skills
    sdir = Path(__file__).parent.parent / "skills"
    if not sdir.exists():
        return
    for f in sdir.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            _custom_skills[f.stem] = data
        except Exception:
            pass

def get_skill(name):
    """Get a skill by name."""
    if name in BUILTIN_SKILLS:
        return BUILTIN_SKILLS[name]
    load_custom()
    return _custom_skills.get(name)

def list_skills():
    """List all available skills."""
    load_custom()
    all_skills = {}
    all_skills.update(BUILTIN_SKILLS)
    all_skills.update(_custom_skills)
    return all_skills

def save_skill(name, prompt, description=""):
    """Save a custom skill."""
    sdir = Path(__file__).parent.parent / "skills"
    sdir.mkdir(parents=True, exist_ok=True)
    data = {"description": description, "prompt": prompt}
    (sdir / f"{name}.json").write_text(json.dumps(data, indent=2))
    _custom_skills[name] = data

def delete_skill(name):
    """Delete a custom skill."""
    sdir = Path(__file__).parent.parent / "skills"
    fpath = sdir / f"{name}.json"
    if fpath.exists():
        fpath.unlink()
        _custom_skills.pop(name, None)
        return True
    return False
