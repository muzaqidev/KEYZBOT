"""Plugin loader — dynamic tool discovery from plugins/ directory."""

import importlib.util
from pathlib import Path

PLUGINS_DIR = Path(__file__).parent.parent / "plugins"
_loaded_plugins = {}  # module_name -> module

def discover():
    """Discover and load all plugin .py files from plugins/ directory."""
    if not PLUGINS_DIR.exists():
        return {}
    for f in sorted(PLUGINS_DIR.glob("*.py")):
        if f.name.startswith("_"):
            continue
        name = f.stem
        if name in _loaded_plugins:
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", str(f))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # Validate plugin has required exports
            if hasattr(mod, "TOOL_DEFS") and hasattr(mod, "TOOL_NAMES") and hasattr(mod, "execute"):
                _loaded_plugins[name] = mod
        except Exception as e:
            print(f"  Plugin load error ({name}): {e}")
    return _loaded_plugins

def get_all_tool_defs():
    """Get TOOL_DEFS from all loaded plugins."""
    discover()
    defs = []
    for mod in _loaded_plugins.values():
        defs.extend(mod.TOOL_DEFS)
    return defs

def get_all_tool_names():
    """Get all plugin tool names."""
    discover()
    names = set()
    for mod in _loaded_plugins.values():
        names.update(mod.TOOL_NAMES)
    return names

def execute(name, args, work_dir=None):
    """Execute a plugin tool by name."""
    discover()
    for mod in _loaded_plugins.values():
        if name in mod.TOOL_NAMES:
            return mod.execute(name, args, work_dir)
    return f"Error: Unknown plugin tool '{name}'"

def list_plugins():
    """List loaded plugins and their tools."""
    discover()
    result = []
    for name, mod in _loaded_plugins.items():
        result.append({
            "name": name,
            "tools": list(mod.TOOL_NAMES),
            "file": str(PLUGINS_DIR / f"{name}.py"),
        })
    return result

def reload():
    """Reload all plugins."""
    _loaded_plugins.clear()
    return discover()
