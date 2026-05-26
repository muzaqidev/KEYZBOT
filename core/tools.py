"""Centralized tool router — shared by CLI and web server."""

import json, time
from tools import bash, file_ops, web, notebook, monitor, image, git_ops, mcp, ask_user, task_tools, cron_tools
from tools import project_detect, lint_test, github, doc_reader
from . import plugins

def get_all_tool_names():
    """Return set of all tool names."""
    names = {"bash"}
    names.update(file_ops._tool_name())
    names.update(web.TOOL_NAMES)
    names.update(notebook.TOOL_NAMES)
    names.update(monitor.TOOL_NAMES)
    names.update(image.TOOL_NAMES)
    names.update(git_ops.TOOL_NAMES)
    names.update(mcp.TOOL_NAMES)
    names.update(ask_user.TOOL_NAMES)
    names.update(task_tools.TOOL_NAMES)
    names.update(cron_tools.TOOL_NAMES)
    names.update(project_detect.TOOL_NAMES)
    names.update(lint_test.TOOL_NAMES)
    names.update(github.TOOL_NAMES)
    names.update(doc_reader.TOOL_NAMES)
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
    elif name in web.TOOL_NAMES:
        return web.execute(name, args)
    elif name in notebook.TOOL_NAMES:
        return notebook.execute(name, args, work_dir)
    elif name in monitor.TOOL_NAMES:
        return monitor.execute(name, args, work_dir)
    elif name in image.TOOL_NAMES:
        return image.execute(name, args, work_dir)
    elif name in git_ops.TOOL_NAMES:
        return git_ops.execute(name, args, work_dir)
    elif name in mcp.TOOL_NAMES:
        return mcp.execute(name, args, work_dir)
    elif name in ask_user.TOOL_NAMES:
        return ask_user.execute(name, args, work_dir)
    elif name in task_tools.TOOL_NAMES:
        return task_tools.execute(name, args, work_dir)
    elif name in cron_tools.TOOL_NAMES:
        return cron_tools.execute(name, args, work_dir)
    elif name in project_detect.TOOL_NAMES:
        return project_detect.execute(name, args, work_dir)
    elif name in lint_test.TOOL_NAMES:
        return lint_test.execute(name, args, work_dir)
    elif name in github.TOOL_NAMES:
        return github.execute(name, args, work_dir)
    elif name in doc_reader.TOOL_NAMES:
        return doc_reader.execute(name, args, work_dir)

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
