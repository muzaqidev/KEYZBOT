"""Network, HTTP, and DNS tools."""

import socket, ssl, subprocess, os, json

TOOL_DEFS = [
    {"type": "function", "function": {"name": "http_request", "description": "Make an HTTP request (GET, POST, PUT, DELETE, PATCH). Returns status, headers, body.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to request"}, "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"], "description": "HTTP method (default GET)"}, "headers": {"type": "string", "description": "Headers as JSON string"}, "body": {"type": "string", "description": "Request body"}, "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "api_test", "description": "Test an API endpoint with various methods, auth headers, and body. Returns full response.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "API endpoint URL"}, "method": {"type": "string", "description": "HTTP method (default GET)"}, "auth": {"type": "string", "description": "Auth header value (e.g. 'Bearer sk-xxx')"}, "content_type": {"type": "string", "description": "Content-Type header (default application/json)"}, "body": {"type": "string", "description": "Request body as JSON string"}, "follow_redirects": {"type": "boolean", "description": "Follow redirects (default true)"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "dns_lookup", "description": "Perform DNS lookup for a domain. Returns A, AAAA, MX, TXT, CNAME records.", "parameters": {"type": "object", "properties": {"domain": {"type": "string", "description": "Domain to lookup"}, "record_type": {"type": "string", "enum": ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA", "ALL"], "description": "DNS record type (default ALL)"}}, "required": ["domain"]}}},
    {"type": "function", "function": {"name": "port_check", "description": "Check if a port is open on a host.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname or IP"}, "port": {"type": "integer", "description": "Port number to check"}, "timeout": {"type": "integer", "description": "Timeout in seconds (default 5)"}}, "required": ["host", "port"]}}},
    {"type": "function", "function": {"name": "port_scan", "description": "Scan common ports on a host. Returns list of open ports.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname or IP"}, "ports": {"type": "string", "description": "Port range or list (e.g. '1-1024', '80,443,8080'). Default: common ports"}, "timeout": {"type": "integer", "description": "Timeout per port in seconds (default 2)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "whois_lookup", "description": "Perform WHOIS lookup for a domain. Returns registration info.", "parameters": {"type": "object", "properties": {"domain": {"type": "string", "description": "Domain name to lookup"}}, "required": ["domain"]}}},
    {"type": "function", "function": {"name": "ssl_check", "description": "Check SSL certificate for a host. Returns certificate details, expiry, and chain info.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname to check"}, "port": {"type": "integer", "description": "Port (default 443)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "ping_host", "description": "Ping a host to check connectivity and latency.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname or IP to ping"}, "count": {"type": "integer", "description": "Number of pings (default 4)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "url_parse", "description": "Parse a URL into its components (scheme, host, port, path, query, fragment).", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to parse"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "curl_parse", "description": "Parse a curl command into structured components.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Curl command string to parse"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "network_interfaces", "description": "List all network interfaces and their IP addresses.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "traceroute", "description": "Run traceroute to a host. Shows network path.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Target host"}, "max_hops": {"type": "integer", "description": "Max hops (default 30)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "download_file", "description": "Download a file from a URL to local disk.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to download"}, "output": {"type": "string", "description": "Local file path to save to"}, "headers": {"type": "string", "description": "Optional headers as JSON string"}}, "required": ["url", "output"]}}},
    {"type": "function", "function": {"name": "upload_file", "description": "Upload a file to a URL via HTTP POST multipart.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "Upload endpoint URL"}, "file_path": {"type": "string", "description": "Local file to upload"}, "field_name": {"type": "string", "description": "Form field name (default 'file')"}}, "required": ["url", "file_path"]}}},
    {"type": "function", "function": {"name": "webhook_send", "description": "Send a webhook payload to a URL (Slack, Discord, custom).", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "Webhook URL"}, "payload": {"type": "string", "description": "JSON payload"}, "content_type": {"type": "string", "description": "Content-Type (default application/json)"}}, "required": ["url", "payload"]}}},
    {"type": "function", "function": {"name": "local_ip", "description": "Get local and public IP addresses.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "http_request":
            import requests
            method = args.get("method", "GET").upper()
            headers = json.loads(args["headers"]) if args.get("headers") else {}
            timeout = args.get("timeout", 30)
            resp = requests.request(method, args["url"], headers=headers, data=args.get("body"), timeout=timeout, allow_redirects=True)
            return f"HTTP {resp.status_code}\n\nHeaders:\n{json.dumps(dict(resp.headers), indent=2)}\n\nBody:\n{resp.text[:5000]}"

        elif name == "api_test":
            import requests
            method = args.get("method", "GET").upper()
            headers = {}
            if args.get("auth"):
                headers["Authorization"] = args["auth"]
            headers["Content-Type"] = args.get("content_type", "application/json")
            resp = requests.request(method, args["url"], headers=headers, data=args.get("body"), timeout=30, allow_redirects=args.get("follow_redirects", True))
            try:
                body = json.dumps(resp.json(), indent=2)[:5000]
            except Exception:
                body = resp.text[:5000]
            return f"HTTP {resp.status_code} ({resp.elapsed.total_seconds():.2f}s)\n\n{body}"

        elif name == "dns_lookup":
            domain = args["domain"]
            result = subprocess.run(["nslookup", domain], capture_output=True, text=True, timeout=10)
            return result.stdout or result.stderr or "(no result)"

        elif name == "port_check":
            host = args["host"]
            port = args["port"]
            timeout = args.get("timeout", 5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                s.connect((host, port))
                s.close()
                return f"Port {port} on {host}: OPEN"
            except (socket.timeout, ConnectionRefusedError, OSError):
                return f"Port {port} on {host}: CLOSED or FILTERED"

        elif name == "port_scan":
            host = args["host"]
            timeout = args.get("timeout", 2)
            ports_str = args.get("ports", "")
            if not ports_str:
                ports = [21, 22, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080, 8443, 3000, 5000, 9090]
            elif "-" in ports_str:
                start, end = ports_str.split("-")
                ports = range(int(start), int(end) + 1)
            else:
                ports = [int(p.strip()) for p in ports_str.split(",")]
            open_ports = []
            for port in ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                try:
                    s.connect((host, int(port)))
                    open_ports.append(port)
                except:
                    pass
                finally:
                    s.close()
            return f"Open ports on {host}: {open_ports}" if open_ports else f"No open ports found on {host}"

        elif name == "whois_lookup":
            result = subprocess.run(["whois", args["domain"]], capture_output=True, text=True, timeout=15)
            return (result.stdout or result.stderr)[:5000]

        elif name == "ssl_check":
            host = args["host"]
            port = args.get("port", 443)
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(10)
                s.connect((host, port))
                cert = s.getpeercert()
            lines = []
            for k, v in cert.get("subject", ()):
                if k == "commonName":
                    lines.append(f"Subject: {v}")
            for k, v in cert.get("issuer", ()):
                if k == "organizationName":
                    lines.append(f"Issuer: {v}")
            lines.append(f"Valid from: {cert.get('notBefore', 'N/A')}")
            lines.append(f"Valid until: {cert.get('notAfter', 'N/A')}")
            san = [v for t, v in cert.get("subjectAltName", ()) if t == "DNS"]
            if san:
                lines.append(f"SANs: {', '.join(san[:10])}")
            return "\n".join(lines)

        elif name == "ping_host":
            count = args.get("count", 4)
            result = subprocess.run(["ping", "-c", str(count), args["host"]], capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr

        elif name == "url_parse":
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(args["url"])
            qs = parse_qs(parsed.query)
            lines = [
                f"Scheme: {parsed.scheme}",
                f"Host: {parsed.hostname or 'N/A'}",
                f"Port: {parsed.port or 'default'}",
                f"Path: {parsed.path or '/'}",
                f"Query: {json.dumps(qs, indent=2) if qs else 'none'}",
                f"Fragment: {parsed.fragment or 'none'}",
            ]
            return "\n".join(lines)

        elif name == "curl_parse":
            import shlex
            parts = shlex.split(args["command"])
            lines = []
            i = 0
            while i < len(parts):
                if parts[i] == "curl":
                    i += 1
                    continue
                elif parts[i] == "-X":
                    lines.append(f"Method: {parts[i+1]}")
                    i += 2
                elif parts[i] == "-H":
                    lines.append(f"Header: {parts[i+1]}")
                    i += 2
                elif parts[i] == "-d":
                    lines.append(f"Body: {parts[i+1]}")
                    i += 2
                elif parts[i].startswith("http"):
                    lines.append(f"URL: {parts[i]}")
                    i += 1
                else:
                    lines.append(f"Flag: {parts[i]}")
                    i += 1
            return "\n".join(lines) or "(no curl components found)"

        elif name == "network_interfaces":
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
            return result.stdout[:5000] or "(no output)"

        elif name == "traceroute":
            max_hops = args.get("max_hops", 30)
            result = subprocess.run(["traceroute", "-m", str(max_hops), args["host"]], capture_output=True, text=True, timeout=60)
            return result.stdout[:5000] or result.stderr[:5000]

        elif name == "download_file":
            import requests
            headers = json.loads(args["headers"]) if args.get("headers") else {}
            resp = requests.get(args["url"], headers=headers, stream=True, timeout=60)
            resp.raise_for_status()
            with open(args["output"], "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            size = os.path.getsize(args["output"])
            return f"Downloaded to {args['output']} ({size} bytes)"

        elif name == "upload_file":
            import requests
            field = args.get("field_name", "file")
            with open(args["file_path"], "rb") as f:
                resp = requests.post(args["url"], files={field: f}, timeout=60)
            return f"HTTP {resp.status_code}\n{resp.text[:2000]}"

        elif name == "webhook_send":
            import requests
            headers = {"Content-Type": args.get("content_type", "application/json")}
            resp = requests.post(args["url"], headers=headers, data=args["payload"], timeout=15)
            return f"HTTP {resp.status_code}\n{resp.text[:2000]}"

        elif name == "local_ip":
            import requests
            lines = []
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                lines.append(f"Local IP: {local_ip}")
                lines.append(f"Hostname: {hostname}")
            except Exception as e:
                lines.append(f"Local: {e}")
            try:
                resp = requests.get("https://api.ipify.org?format=json", timeout=5)
                lines.append(f"Public IP: {resp.json()['ip']}")
            except Exception:
                lines.append("Public IP: (unavailable)")
            return "\n".join(lines)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
