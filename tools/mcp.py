"""MCP (Model Context Protocol) — connect to MCP servers for extended tools."""

import json, subprocess, os
from pathlib import Path

# MCP server registry
_servers = {}  # name -> {"command": str, "args": list, "tools": list}

# KEYZBOT's own MCP config (not dependent on OpenClaude)
_KB_DIR = Path(__file__).parent.parent
_KB_MCP = _KB_DIR / "mcp.json"
_KB_ENV = _KB_DIR / ".env"

def _load_dotenv(env_file):
    """Load environment variables from .env file."""
    env = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def _load_config():
    """Load MCP servers from KEYZBOT's mcp.json."""
    global _servers
    settings = _KB_MCP
    if not settings.exists():
        return
    try:
        cfg = json.loads(settings.read_text())
        mcp = cfg.get("mcpServers", {})
        # Load .env for auto-injecting API keys
        dotenv = _load_dotenv(_KB_ENV)
        for name, server_cfg in mcp.items():
            env = server_cfg.get("env", {})
            # Auto-inject from .env if key is placeholder or empty
            for k, v in env.items():
                if v.startswith("YOUR_") or v == "":
                    env[k] = dotenv.get(k, v)
            _servers[name] = {
                "command": server_cfg.get("command", ""),
                "args": server_cfg.get("args", []),
                "env": env,
                "tools": [],
            }
    except Exception:
        pass


def _discover_tools(server_name):
    """Connect to MCP server and fetch available tools via tools/list."""
    server = _servers.get(server_name)
    if not server:
        return []
    cmd = server["command"]
    args = server.get("args", [])
    env = os.environ.copy()
    env.update(server.get("env", {}))

    init = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "keyzbot", "version": "9.1"}
    }}
    # Send initialized notification
    initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    # Request tools list
    list_req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    input_data = json.dumps(init) + "\n" + json.dumps(initialized) + "\n" + json.dumps(list_req) + "\n"

    try:
        full_cmd = [cmd] + args
        proc = subprocess.Popen(
            full_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, text=True
        )
        stdout, stderr = proc.communicate(input=input_data, timeout=15)
        for line in stdout.strip().split("\n"):
            try:
                resp = json.loads(line)
                if "result" in resp and "tools" in resp["result"]:
                    tools = resp["result"]["tools"]
                    server["tools"] = tools
                    return tools
            except json.JSONDecodeError:
                continue
    except Exception:
        pass
    return []

def list_servers():
    """List configured MCP servers and auto-discover their tools."""
    _load_config()
    if not _servers:
        return "No MCP servers configured. Add mcpServers to KEYZBOT/mcp.json"
    lines = []
    for name, info in _servers.items():
        # Auto-discover tools if not yet discovered
        if not info["tools"]:
            _discover_tools(name)
        cmd = f"{info['command']} {' '.join(info['args'])}"
        tool_count = len(info["tools"])
        status = "✅" if tool_count > 0 else "❌"
        tool_names = ", ".join([t.get("name", "?") for t in info["tools"][:5]])
        if tool_count > 5:
            tool_names += f" +{tool_count - 5} more"
        lines.append(f"{status} {name}: {cmd} ({tool_count} tools)")
        if tool_names:
            lines.append(f"   Tools: {tool_names}")
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
            "clientInfo": {"name": "keyzbot", "version": "9.1"}
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
        server = args.get("server", "")
        # Auto-discover tools if needed
        if server in _servers and not _servers[server]["tools"]:
            _discover_tools(server)
        return call_tool(server, args.get("tool", ""), args.get("arguments"))
    return f"Unknown MCP tool: {name}"
