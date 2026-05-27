"""Health check and service monitoring tools."""

import subprocess, os, time, socket

TOOL_DEFS = [
    {"type": "function", "function": {"name": "health_http", "description": "Check HTTP endpoint health — status, response time, content validation.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}, "expected_status": {"type": "integer", "description": "Expected HTTP status (default 200)"}, "expected_text": {"type": "string", "description": "Text that must be in response body"}, "timeout": {"type": "integer", "description": "Timeout seconds (default 10)"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "health_tcp", "description": "Check if a TCP port is accepting connections.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname"}, "port": {"type": "integer", "description": "Port number"}, "timeout": {"type": "integer", "description": "Timeout seconds (default 5)"}}, "required": ["host", "port"]}}},
    {"type": "function", "function": {"name": "health_dns", "description": "Check DNS resolution for a domain.", "parameters": {"type": "object", "properties": {"domain": {"type": "string", "description": "Domain to resolve"}, "expected_ip": {"type": "string", "description": "Expected IP address"}}, "required": ["domain"]}}},
    {"type": "function", "function": {"name": "health_ssl", "description": "Check SSL certificate validity and expiry.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname"}, "warn_days": {"type": "integer", "description": "Warn if expiring within N days (default 30)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "health_disk", "description": "Check disk space usage and warn if above threshold.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path to check (default /)"}, "warn_percent": {"type": "integer", "description": "Warn if usage above N% (default 80)"}}, "required": []}}},
    {"type": "function", "function": {"name": "health_memory", "description": "Check memory usage and warn if above threshold.", "parameters": {"type": "object", "properties": {"warn_percent": {"type": "integer", "description": "Warn if usage above N% (default 80)"}}, "required": []}}},
    {"type": "function", "function": {"name": "health_cpu", "description": "Check CPU load average.", "parameters": {"type": "object", "properties": {"warn_load": {"type": "number", "description": "Warn if 1min load above N (default 4.0)"}}, "required": []}}},
    {"type": "function", "function": {"name": "health_process", "description": "Check if a specific process is running.", "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Process name to check"}, "restart_cmd": {"type": "string", "description": "Command to run if not found (optional)"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "health_service", "description": "Check system service status (systemd).", "parameters": {"type": "object", "properties": {"service": {"type": "string", "description": "Service name"}, "restart": {"type": "boolean", "description": "Restart if not running (default false)"}}, "required": ["service"]}}},
    {"type": "function", "function": {"name": "health_url_chain", "description": "Check a URL's redirect chain and validate each hop.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "uptime_monitor", "description": "Monitor a URL's uptime by checking it periodically.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to monitor"}, "interval": {"type": "integer", "description": "Check interval seconds (default 60)"}, "count": {"type": "integer", "description": "Number of checks (default 10)"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "health_report", "description": "Run all health checks and generate a system report.", "parameters": {"type": "object", "properties": {"urls": {"type": "array", "items": {"type": "string"}, "description": "URLs to check"}}, "required": []}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        import requests

        if name == "health_http":
            url = args["url"]
            expected = args.get("expected_status", 200)
            expected_text = args.get("expected_text", "")
            timeout = args.get("timeout", 10)
            start = time.time()
            try:
                resp = requests.get(url, timeout=timeout)
                elapsed = (time.time() - start) * 1000
                checks = []
                if resp.status_code == expected:
                    checks.append(f"Status: OK ({resp.status_code})")
                else:
                    checks.append(f"Status: FAIL (got {resp.status_code}, expected {expected})")
                if expected_text:
                    if expected_text in resp.text:
                        checks.append(f"Content: OK (found '{expected_text}')")
                    else:
                        checks.append(f"Content: FAIL ('{expected_text}' not found)")
                checks.append(f"Response time: {elapsed:.0f}ms")
                checks.append(f"Size: {len(resp.content)//1024}KB")
                return "\n".join(checks)
            except requests.exceptions.Timeout:
                return f"FAIL: Timeout after {timeout}s"
            except Exception as e:
                return f"FAIL: {e}"

        elif name == "health_tcp":
            host = args["host"]
            port = args["port"]
            timeout = args.get("timeout", 5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            start = time.time()
            try:
                s.connect((host, port))
                elapsed = (time.time() - start) * 1000
                s.close()
                return f"OK: {host}:{port} accepting connections ({elapsed:.0f}ms)"
            except Exception as e:
                return f"FAIL: {host}:{port} — {e}"

        elif name == "health_dns":
            domain = args["domain"]
            expected = args.get("expected_ip", "")
            try:
                ip = socket.gethostbyname(domain)
                if expected:
                    if ip == expected:
                        return f"OK: {domain} resolves to {ip}"
                    else:
                        return f"FAIL: {domain} resolves to {ip}, expected {expected}"
                return f"OK: {domain} resolves to {ip}"
            except Exception as e:
                return f"FAIL: DNS resolution failed — {e}"

        elif name == "health_ssl":
            import ssl
            host = args["host"]
            warn_days = args.get("warn_days", 30)
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(10)
                s.connect((host, 443))
                cert = s.getpeercert()
            from datetime import datetime
            expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days_left = (expires - datetime.utcnow()).days
            if days_left < 0:
                return f"EXPIRED: Certificate expired {abs(days_left)} days ago"
            elif days_left < warn_days:
                return f"WARNING: Certificate expires in {days_left} days ({expires.strftime('%Y-%m-%d')})"
            else:
                return f"OK: Certificate valid for {days_left} more days (expires {expires.strftime('%Y-%m-%d')})"

        elif name == "health_disk":
            import shutil
            path = args.get("path", "/")
            warn = args.get("warn_percent", 80)
            usage = shutil.disk_usage(path)
            percent = usage.used * 100 // usage.total
            status = "WARNING" if percent >= warn else "OK"
            return f"{status}: {percent}% used ({usage.used//(1024**3)}GB / {usage.total//(1024**3)}GB)"

        elif name == "health_memory":
            warn = args.get("warn_percent", 80)
            with open("/proc/meminfo") as f:
                info = {}
                for line in f.readlines()[:10]:
                    parts = line.split()
                    info[parts[0].rstrip(":")] = int(parts[1])
            total = info.get("MemTotal", 0)
            available = info.get("MemAvailable", 0)
            used = total - available
            percent = used * 100 // total if total else 0
            status = "WARNING" if percent >= warn else "OK"
            return f"{status}: {percent}% used ({used//1024}MB / {total//1024}MB)"

        elif name == "health_cpu":
            warn = args.get("warn_load", 4.0)
            with open("/proc/loadavg") as f:
                load = f.read().split()
            load_1 = float(load[0])
            cores = os.cpu_count() or 1
            status = "WARNING" if load_1 > warn else "OK"
            return f"{status}: Load {load[0]} {load[1]} {load[2]} ({cores} cores)"

        elif name == "health_process":
            pname = args["name"]
            r = subprocess.run(["pgrep", "-f", pname], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                pids = r.stdout.strip().split("\n")
                return f"OK: {pname} running (PIDs: {', '.join(pids)})"
            else:
                if args.get("restart_cmd"):
                    subprocess.run(args["restart_cmd"], shell=True, capture_output=True, timeout=30)
                    return f"WARNING: {pname} not found — restarted with: {args['restart_cmd']}"
                return f"WARNING: {pname} not running"

        elif name == "health_service":
            service = args["service"]
            r = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True, timeout=5)
            status = r.stdout.strip()
            if status == "active":
                return f"OK: {service} is active"
            else:
                if args.get("restart"):
                    subprocess.run(["systemctl", "restart", service], capture_output=True, timeout=30)
                    return f"WARNING: {service} was {status} — restarted"
                return f"WARNING: {service} is {status}"

        elif name == "health_url_chain":
            resp = requests.get(args["url"], timeout=10, allow_redirects=True)
            lines = []
            for i, r in enumerate(resp.history):
                lines.append(f"  [{r.status_code}] {r.url}")
            lines.append(f"  [{resp.status_code}] {resp.url} (final)")
            return f"Chain ({len(resp.history)} redirects):\n" + "\n".join(lines)

        elif name == "uptime_monitor":
            url = args["url"]
            interval = args.get("interval", 60)
            count = args.get("count", 10)
            results = []
            for i in range(count):
                start = time.time()
                try:
                    resp = requests.get(url, timeout=10)
                    elapsed = (time.time() - start) * 1000
                    results.append({"status": resp.status_code, "ms": round(elapsed), "ok": 200 <= resp.status_code < 400})
                except Exception as e:
                    results.append({"status": 0, "ms": 0, "ok": False, "error": str(e)})
                if i < count - 1:
                    time.sleep(min(interval, 5))  # Cap at 5s for tool use
            up = sum(1 for r in results if r["ok"])
            avg_ms = sum(r["ms"] for r in results if r["ok"]) / max(up, 1)
            return f"Uptime: {up}/{count} ({up*100//count}%)\nAvg response: {avg_ms:.0f}ms\nChecks:\n" + "\n".join(
                f"  {'OK' if r['ok'] else 'FAIL'}: {r['status']} {r['ms']}ms" for r in results
            )

        elif name == "health_report":
            lines = ["=== Health Report ===\n"]
            # System checks
            lines.append("--- System ---")
            lines.append(execute("health_disk", {}, work_dir))
            lines.append(execute("health_memory", {}, work_dir))
            lines.append(execute("health_cpu", {}, work_dir))
            # URL checks
            urls = args.get("urls", [])
            if urls:
                lines.append("\n--- URLs ---")
                for url in urls:
                    lines.append(execute("health_http", {"url": url}, work_dir))
            return "\n".join(lines)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
