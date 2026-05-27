"""Tunnel and proxy tools — expose local ports, ngrok, localtunnel, HTTP proxy."""

import subprocess, os, json, time, signal

TOOL_DEFS = [
    {"type": "function", "function": {"name": "ngrok_start", "description": "Start an ngrok tunnel to expose a local port publicly.", "parameters": {"type": "object", "properties": {"port": {"type": "integer", "description": "Local port to expose"}, "protocol": {"type": "string", "enum": ["http", "tcp", "tls"], "description": "Protocol (default http)"}, "region": {"type": "string", "enum": ["us", "eu", "au", "ap", "sa", "jp", "in"], "description": "Region (default us)"}}, "required": ["port"]}}},
    {"type": "function", "function": {"name": "ngrok_stop", "description": "Stop all ngrok tunnels.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ngrok_status", "description": "Show active ngrok tunnels and their public URLs.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "lt_start", "description": "Start a localtunnel to expose a local port (no account needed).", "parameters": {"type": "object", "properties": {"port": {"type": "integer", "description": "Local port to expose"}, "subdomain": {"type": "string", "description": "Custom subdomain (random if omitted)"}}, "required": ["port"]}}},
    {"type": "function", "function": {"name": "lt_stop", "description": "Stop localtunnel.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ssh_tunnel_start", "description": "Start an SSH tunnel (port forwarding).", "parameters": {"type": "object", "properties": {"local_port": {"type": "integer", "description": "Local port"}, "remote_host": {"type": "string", "description": "Remote host:port"}, "ssh_host": {"type": "string", "description": "SSH server user@host"}, "ssh_key": {"type": "string", "description": "SSH key file"}}, "required": ["local_port", "remote_host", "ssh_host"]}}},
    {"type": "function", "function": {"name": "ssh_tunnel_stop", "description": "Stop an SSH tunnel.", "parameters": {"type": "object", "properties": {"local_port": {"type": "integer", "description": "Local port of the tunnel"}}, "required": ["local_port"]}}},
    {"type": "function", "function": {"name": "proxy_start", "description": "Start a simple HTTP forward proxy on a local port.", "parameters": {"type": "object", "properties": {"port": {"type": "integer", "description": "Port to listen on (default 8888)"}, "upstream": {"type": "string", "description": "Upstream proxy URL (optional)"}}, "required": []}}},
    {"type": "function", "function": {"name": "proxy_stop", "description": "Stop the local HTTP proxy.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "serve_static", "description": "Start a static file server on a local port.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory to serve"}, "port": {"type": "integer", "description": "Port (default 8000)"}}, "required": ["path"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]

_PROCESSES = {}


def execute(name, args, work_dir=None):
    try:
        if name == "ngrok_start":
            port = args["port"]
            protocol = args.get("protocol", "http")
            region = args.get("region", "us")
            cmd = ["ngrok", protocol, str(port), "--region", region, "--log", "stdout"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _PROCESSES[f"ngrok_{port}"] = proc
            time.sleep(3)
            # Try to get the public URL
            try:
                import requests
                resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                tunnels = resp.json().get("tunnels", [])
                urls = [t["public_url"] for t in tunnels]
                return f"ngrok tunnel started\nPublic URLs: {', '.join(urls)}"
            except:
                return f"ngrok tunnel started on port {port} (check ngrok dashboard at http://127.0.0.1:4040)"

        elif name == "ngrok_stop":
            killed = 0
            for k, p in list(_PROCESSES.items()):
                if k.startswith("ngrok_"):
                    p.terminate()
                    del _PROCESSES[k]
                    killed += 1
            # Also kill any orphan ngrok processes
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True, timeout=5)
            return f"Stopped {killed} ngrok tunnel(s)"

        elif name == "ngrok_status":
            try:
                import requests
                resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                tunnels = resp.json().get("tunnels", [])
                if not tunnels:
                    return "(no active tunnels)"
                lines = []
                for t in tunnels:
                    lines.append(f"  {t['name']}: {t['public_url']} -> {t['config']['addr']}")
                return "\n".join(lines)
            except:
                return "(ngrok not running or not installed)"

        elif name == "lt_start":
            port = args["port"]
            cmd = ["lt", "--port", str(port)]
            if args.get("subdomain"):
                cmd += ["--subdomain", args["subdomain"]]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _PROCESSES["lt"] = proc
            time.sleep(3)
            # Try to read the URL from stdout
            try:
                import select
                if select.select([proc.stdout], [], [], 2)[0]:
                    line = proc.stdout.readline().decode().strip()
                    return f"localtunnel started: {line}"
            except:
                pass
            return f"localtunnel started on port {port}"

        elif name == "lt_stop":
            if "lt" in _PROCESSES:
                _PROCESSES["lt"].terminate()
                del _PROCESSES["lt"]
            subprocess.run(["pkill", "-f", "localtunnel"], capture_output=True, timeout=5)
            return "localtunnel stopped"

        elif name == "ssh_tunnel_start":
            local_port = args["local_port"]
            remote = args["remote_host"]
            ssh = args["ssh_host"]
            cmd = ["ssh", "-N", "-L", f"{local_port}:{remote}", "-o", "StrictHostKeyChecking=no"]
            if args.get("ssh_key"):
                cmd += ["-i", args["ssh_key"]]
            cmd.append(ssh)
            proc = subprocess.Popen(cmd)
            _PROCESSES[f"ssh_{local_port}"] = proc
            return f"SSH tunnel: localhost:{local_port} -> {remote} via {ssh}"

        elif name == "ssh_tunnel_stop":
            key = f"ssh_{args['local_port']}"
            if key in _PROCESSES:
                _PROCESSES[key].terminate()
                del _PROCESSES[key]
                return f"SSH tunnel on port {args['local_port']} stopped"
            return "No tunnel found on that port"

        elif name == "proxy_start":
            port = args.get("port", 8888)
            # Simple Python proxy
            proxy_code = f"""
import http.server, socketserver, urllib.request
class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            resp = urllib.request.urlopen(self.path, timeout=10)
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, str(e))
    def log_message(self, *a): pass
with socketserver.TCPServer(('', {port}), ProxyHandler) as httpd:
    httpd.serve_forever()
"""
            proc = subprocess.Popen(["python3", "-c", proxy_code])
            _PROCESSES["proxy"] = proc
            return f"Proxy started on port {port}"

        elif name == "proxy_stop":
            if "proxy" in _PROCESSES:
                _PROCESSES["proxy"].terminate()
                del _PROCESSES["proxy"]
                return "Proxy stopped"
            return "No proxy running"

        elif name == "serve_static":
            path = args["path"]
            port = args.get("port", 8000)
            proc = subprocess.Popen(["python3", "-m", "http.server", str(port), "--directory", path])
            _PROCESSES["static"] = proc
            return f"Serving {path} on http://localhost:{port}"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
