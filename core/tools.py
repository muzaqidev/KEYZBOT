"""Centralized tool router — shared by CLI and web server."""

import json, time
from tools import bash, file_ops, web, notebook, monitor, image, git_ops, mcp, ask_user, task_tools, cron_tools
from tools import project_detect, lint_test, github, doc_reader
from tools import data, network, code_analysis, docker_tools, packages, text, system, archive
from tools import security, media, cloud, workflow, notify, math_tools, ai_tools, regex_tools, git_advanced
from tools import browser, pdf_tools, spreadsheet, mockdata, clipboard, tunnel, healthcheck, docgen, ai_media
from . import plugins

# Registry of all tool modules with their TOOL_NAMES
_TOOL_MODULES = [
    (web, None), (notebook, None), (monitor, None), (image, None),
    (git_ops, None), (mcp, None), (ask_user, None), (task_tools, None),
    (cron_tools, None), (project_detect, None), (lint_test, None),
    (github, None), (doc_reader, None),
    (data, None), (network, None), (code_analysis, None), (docker_tools, None),
    (packages, None), (text, None), (system, None), (archive, None),
    (security, None), (media, None), (cloud, None), (workflow, None),
    (notify, None), (math_tools, None), (ai_tools, None), (regex_tools, None),
    (git_advanced, None),
    (browser, None), (pdf_tools, None), (spreadsheet, None), (mockdata, None),
    (clipboard, None), (tunnel, None), (healthcheck, None), (docgen, None),
    (ai_media, None),
]

def _build_module_map():
    """Build name->module mapping for fast dispatch."""
    mapping = {}
    for mod, _ in _TOOL_MODULES:
        for tname in mod.TOOL_NAMES:
            mapping[tname] = mod
    return mapping

_MODULE_MAP = _build_module_map()

def get_all_tool_names():
    """Return set of all tool names."""
    names = {"bash"}
    names.update(file_ops._tool_name())
    for mod, _ in _TOOL_MODULES:
        names.update(mod.TOOL_NAMES)
    names.update(plugins.get_all_tool_names())
    return names

def execute(name, args, work_dir=None, bot=None):
    """Execute a tool call. Returns result string.

    Args:
        name: Tool name
        args: Tool arguments dict
        work_dir: Working directory
        bot: Agent instance (for spawn_agent, run_skill)

    Returns:
        Tool result as string
    """
    from . import memory, plan, subagents, skills

    # Core tools
    if name == "bash":
        return bash.execute(args, work_dir)
    elif name in file_ops._tool_name():
        return file_ops.execute(name, args, work_dir)

    # All registered tool modules (fast lookup)
    elif name in _MODULE_MAP:
        return _MODULE_MAP[name].execute(name, args, work_dir)

    # Plugin tools
    elif name in plugins.get_all_tool_names():
        return plugins.execute(name, args, work_dir)

    # Memory tools
    elif name == "save_memory":
        fpath = memory.save(
            args.get("name", ""), args.get("content", ""),
            args.get("mtype", "project"), args.get("scope", "private"))
        return f"Memory saved to {fpath}"
    elif name == "load_memory":
        query = args.get("query", "")
        loaded = memory.load(query)
        if loaded:
            return loaded
        results = memory.search(query)
        if results:
            return "\n".join([f"{r['name']}: {r['description']}" for r in results])
        return f"No memories found for: {query}"

    # Plan tools
    elif name == "read_plan":
        content = plan.read()
        return content if content else "No active plan. Use /plan <title> to create one."
    elif name == "update_plan":
        plan.update(args.get("content", ""))
        return "Plan updated"

    # Agent tools
    elif name == "spawn_agent":
        atype = args.get("agent_type", "general-purpose")
        agent_name = args.get("name", f"agent-{int(time.time()) % 10000}")
        task = args.get("task", "")
        bg = args.get("background", True)
        res = subagents.spawn(agent_name, task, atype, bot, work_dir=work_dir, background=bg)
        if bg:
            return f"Agent '{agent_name}' ({atype}) running in background"
        return res.get("result", "No result")

    # Skill tools
    elif name == "run_skill":
        sk = skills.get_skill(args.get("skill_name", ""))
        if sk:
            return f"Skill prompt: {sk.get('prompt', '')}"
        return f"Skill not found: {args.get('skill_name', '')}"

    return f"Error: Unknown tool '{name}'"
