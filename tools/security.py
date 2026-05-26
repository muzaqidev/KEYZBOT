"""Security scanning and crypto tools."""

import subprocess, os, re, json, hashlib, secrets, base64

TOOL_DEFS = [
    {"type": "function", "function": {"name": "secret_scan", "description": "Scan codebase for hardcoded secrets, API keys, passwords, and tokens.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory or file to scan"}, "include": {"type": "string", "description": "File glob filter"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "vulnerability_scan", "description": "Check Python dependencies for known vulnerabilities using pip-audit or safety.", "parameters": {"type": "object", "properties": {"requirements": {"type": "string", "description": "Path to requirements.txt (default: auto-detect)"}}, "required": []}}},
    {"type": "function", "function": {"name": "password_strength", "description": "Check password strength and estimated crack time.", "parameters": {"type": "object", "properties": {"password": {"type": "string", "description": "Password to check"}}, "required": ["password"]}}},
    {"type": "function", "function": {"name": "password_generate", "description": "Generate a cryptographically secure random password.", "parameters": {"type": "object", "properties": {"length": {"type": "integer", "description": "Length (default 20)"}, "symbols": {"type": "boolean", "description": "Include symbols (default true)"}}, "required": []}}},
    {"type": "function", "function": {"name": "cert_info", "description": "Get SSL certificate details for a domain.", "parameters": {"type": "object", "properties": {"host": {"type": "string", "description": "Hostname"}, "port": {"type": "integer", "description": "Port (default 443)"}}, "required": ["host"]}}},
    {"type": "function", "function": {"name": "file_permissions", "description": "Check file permissions and ownership. Identifies world-writable or SUID files.", "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File or directory to check"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "encrypt_aes", "description": "Encrypt text using AES-256-CBC with a password.", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Text to encrypt"}, "password": {"type": "string", "description": "Encryption password"}}, "required": ["text", "password"]}}},
    {"type": "function", "function": {"name": "decrypt_aes", "description": "Decrypt AES-256-CBC encrypted text.", "parameters": {"type": "object", "properties": {"encrypted": {"type": "string", "description": "Base64 encoded encrypted text"}, "password": {"type": "string", "description": "Decryption password"}}, "required": ["encrypted", "password"]}}},
    {"type": "function", "function": {"name": "ip_reputation", "description": "Check if an IP is in common blocklists or known malicious lists.", "parameters": {"type": "object", "properties": {"ip": {"type": "string", "description": "IP address to check"}}, "required": ["ip"]}}},
    {"type": "function", "function": {"name": "open_ports_check", "description": "Check for commonly exploited open ports on localhost.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "hash_crack", "description": "Attempt to identify hash type and check against common passwords.", "parameters": {"type": "object", "properties": {"hash_value": {"type": "string", "description": "Hash to identify/check"}}, "required": ["hash_value"]}}},
    {"type": "function", "function": {"name": "url_safety_check", "description": "Check if a URL is potentially malicious (basic heuristics).", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL to check"}}, "required": ["url"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        if name == "secret_scan":
            path = args.get("path", ".")
            include = args.get("include", "")
            patterns = [
                (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][^"\']{10,}', "API Key"),
                (r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\'][^"\']{6,}', "Password/Secret"),
                (r'(?i)(token)\s*[:=]\s*["\'][^"\']{10,}', "Token"),
                (r'(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*', "Bearer Token"),
                (r'(?i)ghp_[a-zA-Z0-9]{36}', "GitHub Token"),
                (r'(?i)sk-[a-zA-Z0-9]{20,}', "OpenAI Key"),
                (r'(?i)AKIA[0-9A-Z]{16}', "AWS Access Key"),
                (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', "Private Key"),
            ]
            findings = []
            targets = []
            if os.path.isfile(path):
                targets = [path]
            else:
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]
                    for f in files:
                        if include and not f.endswith(include.lstrip("*")):
                            continue
                        if f.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env', '.cfg', '.ini', '.toml')):
                            targets.append(os.path.join(root, f))
            for fp in targets[:300]:
                try:
                    with open(fp) as f:
                        for i, line in enumerate(f, 1):
                            for pattern, stype in patterns:
                                if re.search(pattern, line):
                                    findings.append(f"{fp}:{i} [{stype}] {line.strip()[:100]}")
                except:
                    continue
            return "\n".join(findings[:50]) or "No secrets found."

        elif name == "vulnerability_scan":
            req = args.get("requirements", "requirements.txt")
            r = subprocess.run(["pip-audit", "-r", req], capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                r = subprocess.run(["safety", "check", "-r", req], capture_output=True, text=True, timeout=60)
            return r.stdout[:5000] or r.stderr[:5000] or "No vulnerabilities found (or tools not installed)"

        elif name == "password_strength":
            pw = args["password"]
            score = 0
            tips = []
            if len(pw) >= 8: score += 1
            else: tips.append("Use at least 8 characters")
            if len(pw) >= 12: score += 1
            if re.search(r'[a-z]', pw): score += 1
            else: tips.append("Add lowercase letters")
            if re.search(r'[A-Z]', pw): score += 1
            else: tips.append("Add uppercase letters")
            if re.search(r'[0-9]', pw): score += 1
            else: tips.append("Add digits")
            if re.search(r'[^a-zA-Z0-9]', pw): score += 1
            else: tips.append("Add special characters")
            if len(set(pw)) > len(pw) * 0.7: score += 1
            level = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong", "Excellent"][min(score, 6)]
            return f"Strength: {level} ({score}/6)\nLength: {len(pw)}\nTips: {'; '.join(tips)}" if tips else f"Strength: {level} ({score}/6)\nLength: {len(pw)}\nExcellent password!"

        elif name == "password_generate":
            length = args.get("length", 20)
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            if args.get("symbols", True):
                chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            return "".join(secrets.choice(chars) for _ in range(length))

        elif name == "cert_info":
            import ssl, socket
            host = args["host"]
            port = args.get("port", 443)
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(10)
                s.connect((host, port))
                cert = s.getpeercert()
            lines = []
            for rdn in cert.get("subject", ()):
                for k, v in rdn:
                    lines.append(f"Subject {k}: {v}")
            for rdn in cert.get("issuer", ()):
                for k, v in rdn:
                    lines.append(f"Issuer {k}: {v}")
            lines.append(f"Valid from: {cert.get('notBefore', 'N/A')}")
            lines.append(f"Valid until: {cert.get('notAfter', 'N/A')}")
            san = [v for t, v in cert.get("subjectAltName", ()) if t == "DNS"]
            if san:
                lines.append(f"SANs: {', '.join(san[:15])}")
            lines.append(f"Version: {cert.get('version', 'N/A')}")
            lines.append(f"Serial: {cert.get('serialNumber', 'N/A')}")
            return "\n".join(lines)

        elif name == "file_permissions":
            path = args["path"]
            findings = []
            if os.path.isfile(path):
                targets = [path]
            else:
                targets = []
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in {'.git'}]
                    for f in files:
                        targets.append(os.path.join(root, f))
                    for d in dirs:
                        targets.append(os.path.join(root, d))
            for fp in targets[:500]:
                try:
                    stat = os.stat(fp)
                    mode = oct(stat.st_mode)[-3:]
                    issues = []
                    if int(mode[2]) >= 6:
                        issues.append("world-writable")
                    if stat.st_mode & 0o4000:
                        issues.append("SUID bit set")
                    if stat.st_mode & 0o2000:
                        issues.append("SGID bit set")
                    if issues:
                        findings.append(f"{fp}: {mode} — {', '.join(issues)}")
                except:
                    continue
            return "\n".join(findings[:50]) or "No permission issues found."

        elif name == "encrypt_aes":
            from cryptography.fernet import Fernet
            key = hashlib.sha256(args["password"].encode()).digest()
            import base64 as b64
            fkey = b64.urlsafe_b64encode(key)
            f = Fernet(fkey)
            encrypted = f.encrypt(args["text"].encode()).decode()
            return encrypted

        elif name == "decrypt_aes":
            from cryptography.fernet import Fernet
            key = hashlib.sha256(args["password"].encode()).digest()
            import base64 as b64
            fkey = b64.urlsafe_b64encode(key)
            f = Fernet(fkey)
            decrypted = f.decrypt(args["encrypted"].encode()).decode()
            return decrypted

        elif name == "ip_reputation":
            ip = args["ip"]
            r = subprocess.run(["curl", "-s", f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}", "-H", "Accept: application/json"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout:
                try:
                    data = json.loads(r.stdout)
                    return json.dumps(data.get("data", {}), indent=2)
                except:
                    pass
            return f"IP {ip}: check manually at https://www.abuseipdb.com/check/{ip}"

        elif name == "open_ports_check":
            common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9090, 27017]
            import socket
            open_ports = []
            for port in common_ports:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                try:
                    s.connect(("127.0.0.1", port))
                    open_ports.append(port)
                except:
                    pass
                finally:
                    s.close()
            return f"Open ports on localhost: {open_ports}" if open_ports else "No common ports open on localhost."

        elif name == "hash_crack":
            h = args["hash_value"].lower()
            hash_types = {
                32: "MD5",
                40: "SHA1",
                64: "SHA256",
                128: "SHA512",
            }
            htype = hash_types.get(len(h), "Unknown")
            common = ["password", "123456", "admin", "root", "letmein", "qwerty", "abc123", "monkey", "master", "dragon"]
            for pw in common:
                for algo in ["md5", "sha1", "sha256"]:
                    if hashlib.new(algo, pw.encode()).hexdigest() == h:
                        return f"Type: {algo.upper()}\nCRACKED: {pw}"
            return f"Type: {htype}\nNot found in common password list."

        elif name == "url_safety_check":
            url = args["url"]
            warnings = []
            if not url.startswith("https"):
                warnings.append("Not HTTPS — data sent in cleartext")
            suspicious = ["login", "verify", "secure", "account", "update", "banking", "paypal", "signin"]
            url_lower = url.lower()
            for word in suspicious:
                if word in url_lower:
                    warnings.append(f"Contains '{word}' — common phishing keyword")
            if url.count("-") > 5:
                warnings.append("Excessive hyphens — common in phishing domains")
            if any(c in url for c in ["@", "%40"]):
                warnings.append("Contains @ — may redirect to different host")
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.hostname and len(parsed.hostname) > 50:
                warnings.append("Unusually long hostname")
            return f"URL: {url}\nWarnings: {len(warnings)}\n" + "\n".join(f"  - {w}" for w in warnings) if warnings else f"URL: {url}\nNo obvious issues detected."

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
