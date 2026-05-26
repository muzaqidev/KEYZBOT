"""MCP (Model Context Protocol) — connect to MCP servers for extended tools."""

import json, subprocess, os
from pathlib import Path

# MCP server registry
_servers = {}  # name -> {"command": str, "args": list, "tools": list}

def _load_config():
    """Load MCP servers from settings.json."""
    global _servers
    settings = Path.home() / ".openclaude" / "settings.json"
    if not settings.exists():
        return
    try:
        cfg = json.loads(settings.read_text())
        mcp = cfg.get("mcpServers", {})
        for name, server_cfg in mcp.items():
            _servers[name] = {
                "command": server_cfg.get("command", ""),
                "args": server_cfg.get("args", []),
                "env": server_cfg.get("env", {}),
                "tools": [],
            }
    except Exception:
        pass

def list_servers():
    """List configured MCP servers."""
    _load_config()
    if not _servers:
        return "No MCP servers configured. Add mcpServers to ~/.openclaude/settings.json"
    lines = []
    for name, info in _servers.items():
        cmd = f"{info['command']} {' '.join(info['args'])}"
        lines.append(f"- {name}: {cmd} ({len(info['tools'])} tools)")
    return "\n".join(lines)

def call_tool(server_name, tool_name, arguments=None):
    """Call a tool on an MCP server."""
    _load_config()
    server = _servers.get(server_name)
    if not server:
        return f"MCP server not found: {server_name}"
    cmd = server["command"]
    args = server.get("args", [])
    env = os.environ.copy()
    env.update(server.get("env", {}))

    # Build MCP JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }

    try:
        full_cmd = [cmd] + args
        proc = subprocess.Popen(
            full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, text=True
        )
        # Send initialize first
        init = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "keyzbot", "version": "7.0"}
        }}
        input_data = json.dumps(init) + "\n" + json.dumps(request) + "\n"
        stdout, stderr = proc.communicate(input=input_data, timeout=30)
        # Parse response lines
        for line in stdout.strip().split("\n"):
            try:
                resp = json.loads(line)
                if "result" in resp:
                    content = resp["result"].get("content", [])
                    texts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    return "\n".join(texts) if texts else json.dumps(resp["result"])
            except json.JSONDecodeError:
                continue
        return f"MCP response: {stdout[:500]}" if stdout else f"MCP error: {stderr[:500]}"
    except subprocess.TimeoutExpired:
        return f"MCP server timeout: {server_name}"
    except Exception as e:
        return f"MCP error: {e}"

def list_tools(server_name=None):
    """List tools available on an MCP server."""
    _load_config()
    if server_name:
        server = _servers.get(server_name)
        if not server:
            return f"MCP server not found: {server_name}"
        return f"Server {server_name}: {len(server['tools'])} tools (use mcp_call to invoke)"
    lines = []
    for name, info in _servers.items():
        lines.append(f"- {name}: {' '.join([info['command']] + info['args'])}")
    return "\n".join(lines) if lines else "No MCP servers"

# Tool definitions
TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "mcp_list",
            "description": "List available MCP (Model Context Protocol) servers and their tools.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mcp_call",
            "description": "Call a tool on an MCP server. Use mcp_list first to see available servers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server": {"type": "string", "description": "MCP server name"},
                    "tool": {"type": "string", "description": "Tool name to call"},
                    "arguments": {"type": "object", "description": "Tool arguments"}
                },
                "required": ["server", "tool"]
            }
        }
    }
]

TOOL_NAMES = {"mcp_list", "mcp_call"}

def execute(name, args, work_dir=None):
    if name == "mcp_list":
        return list_servers()
    elif name == "mcp_call":
        return call_tool(args.get("server", ""), args.get("tool", ""), args.get("arguments"))
    return f"Unknown MCP tool: {name}"
