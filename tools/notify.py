"""Notification and messaging tools."""

import subprocess, os

TOOL_DEFS = [
    {"type": "function", "function": {"name": "send_email", "description": "Send an email via SMTP.", "parameters": {"type": "object", "properties": {"to": {"type": "string", "description": "Recipient email"}, "subject": {"type": "string", "description": "Email subject"}, "body": {"type": "string", "description": "Email body"}, "smtp_host": {"type": "string", "description": "SMTP server (default: from env SMTP_HOST)"}, "smtp_port": {"type": "integer", "description": "SMTP port (default: 587)"}, "from_addr": {"type": "string", "description": "From address (default: from env SMTP_FROM)"}}, "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {"name": "ntfy_send", "description": "Send a notification via ntfy.sh (free push notifications).", "parameters": {"type": "object", "properties": {"topic": {"type": "string", "description": "ntfy topic/channel name"}, "message": {"type": "string", "description": "Notification message"}, "title": {"type": "string", "description": "Notification title"}, "priority": {"type": "string", "enum": ["min", "low", "default", "high", "urgent"], "description": "Priority level"}, "tags": {"type": "string", "description": "Tags/emojis (comma-separated)"}}, "required": ["topic", "message"]}}},
    {"type": "function", "function": {"name": "telegram_send", "description": "Send a message via Telegram bot.", "parameters": {"type": "object", "properties": {"bot_token": {"type": "string", "description": "Bot token (default: from env TELEGRAM_TOKEN)"}, "chat_id": {"type": "string", "description": "Chat ID (default: from env TELEGRAM_CHAT_ID)"}, "message": {"type": "string", "description": "Message text"}, "parse_mode": {"type": "string", "enum": ["HTML", "Markdown", "MarkdownV2"], "description": "Parse mode"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "discord_send", "description": "Send a message to Discord webhook.", "parameters": {"type": "object", "properties": {"webhook_url": {"type": "string", "description": "Discord webhook URL (default: from env DISCORD_WEBHOOK)"}, "message": {"type": "string", "description": "Message text"}, "username": {"type": "string", "description": "Bot display name"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "slack_send", "description": "Send a message to Slack webhook.", "parameters": {"type": "object", "properties": {"webhook_url": {"type": "string", "description": "Slack webhook URL (default: from env SLACK_WEBHOOK)"}, "message": {"type": "string", "description": "Message text"}, "channel": {"type": "string", "description": "Channel override"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "pushover_send", "description": "Send push notification via Pushover.", "parameters": {"type": "object", "properties": {"token": {"type": "string", "description": "App token (default: from env PUSHOVER_TOKEN)"}, "user": {"type": "string", "description": "User key (default: from env PUSHOVER_USER)"}, "message": {"type": "string", "description": "Message text"}, "title": {"type": "string", "description": "Notification title"}, "priority": {"type": "string", "enum": ["lowest", "low", "normal", "high", "emergency"], "description": "Priority"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "gotify_send", "description": "Send notification to a Gotify server.", "parameters": {"type": "object", "properties": {"server": {"type": "string", "description": "Gotify server URL (default: from env GOTIFY_URL)"}, "token": {"type": "string", "description": "App token (default: from env GOTIFY_TOKEN)"}, "message": {"type": "string", "description": "Message text"}, "title": {"type": "string", "description": "Title"}, "priority": {"type": "integer", "description": "Priority 0-10 (default 5)"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "toast_notify", "description": "Send a desktop notification using notify-send (Linux) or termux-notification (Termux).", "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Notification title"}, "message": {"type": "string", "description": "Notification body"}, "urgency": {"type": "string", "enum": ["low", "normal", "critical"], "description": "Urgency level (default normal)"}}, "required": ["title", "message"]}}},
    {"type": "function", "function": {"name": "bark_send", "description": "Send push notification via Bark (iOS).", "parameters": {"type": "object", "properties": {"server": {"type": "string", "description": "Bark server URL (default: from env BARK_URL)"}, "key": {"type": "string", "description": "Device key (default: from env BARK_KEY)"}, "title": {"type": "string", "description": "Title"}, "message": {"type": "string", "description": "Message"}}, "required": ["message"]}}},
]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]


def execute(name, args, work_dir=None):
    try:
        import requests

        if name == "send_email":
            import smtplib
            from email.mime.text import MIMEText
            host = args.get("smtp_host") or os.environ.get("SMTP_HOST", "")
            port = args.get("smtp_port", 587)
            from_addr = args.get("from_addr") or os.environ.get("SMTP_FROM", "")
            if not host:
                return "Error: SMTP_HOST not set"
            msg = MIMEText(args["body"])
            msg["Subject"] = args["subject"]
            msg["From"] = from_addr
            msg["To"] = args["to"]
            with smtplib.SMTP(host, port) as s:
                s.starttls()
                user = os.environ.get("SMTP_USER", "")
                pwd = os.environ.get("SMTP_PASS", "")
                if user and pwd:
                    s.login(user, pwd)
                s.send_message(msg)
            return f"Email sent to {args['to']}"

        elif name == "ntfy_send":
            topic = args["topic"]
            headers = {}
            if args.get("title"):
                headers["Title"] = args["title"]
            if args.get("priority"):
                headers["Priority"] = args["priority"]
            if args.get("tags"):
                headers["Tags"] = args["tags"]
            resp = requests.post(f"https://ntfy.sh/{topic}", headers=headers, data=args["message"], timeout=10)
            return f"Notification sent to ntfy.sh/{topic} (HTTP {resp.status_code})"

        elif name == "telegram_send":
            token = args.get("bot_token") or os.environ.get("TELEGRAM_TOKEN", "")
            chat_id = args.get("chat_id") or os.environ.get("TELEGRAM_CHAT_ID", "")
            if not token or not chat_id:
                return "Error: TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set"
            payload = {"chat_id": chat_id, "text": args["message"]}
            if args.get("parse_mode"):
                payload["parse_mode"] = args["parse_mode"]
            resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=10)
            return f"Telegram message sent (HTTP {resp.status_code})"

        elif name == "discord_send":
            url = args.get("webhook_url") or os.environ.get("DISCORD_WEBHOOK", "")
            if not url:
                return "Error: DISCORD_WEBHOOK not set"
            payload = {"content": args["message"]}
            if args.get("username"):
                payload["username"] = args["username"]
            resp = requests.post(url, json=payload, timeout=10)
            return f"Discord message sent (HTTP {resp.status_code})"

        elif name == "slack_send":
            url = args.get("webhook_url") or os.environ.get("SLACK_WEBHOOK", "")
            if not url:
                return "Error: SLACK_WEBHOOK not set"
            payload = {"text": args["message"]}
            if args.get("channel"):
                payload["channel"] = args["channel"]
            resp = requests.post(url, json=payload, timeout=10)
            return f"Slack message sent (HTTP {resp.status_code})"

        elif name == "pushover_send":
            token = args.get("token") or os.environ.get("PUSHOVER_TOKEN", "")
            user = args.get("user") or os.environ.get("PUSHOVER_USER", "")
            if not token or not user:
                return "Error: PUSHOVER_TOKEN and PUSHOVER_USER must be set"
            payload = {"token": token, "user": user, "message": args["message"]}
            if args.get("title"): payload["title"] = args["title"]
            if args.get("priority"): payload["priority"] = args["priority"]
            resp = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
            return f"Pushover notification sent (HTTP {resp.status_code})"

        elif name == "gotify_send":
            server = args.get("server") or os.environ.get("GOTIFY_URL", "")
            token = args.get("token") or os.environ.get("GOTIFY_TOKEN", "")
            if not server:
                return "Error: GOTIFY_URL not set"
            payload = {"message": args["message"], "title": args.get("title", "KEYZBOT"), "priority": args.get("priority", 5)}
            resp = requests.post(f"{server}/message", params={"token": token}, json=payload, timeout=10)
            return f"Gotify notification sent (HTTP {resp.status_code})"

        elif name == "toast_notify":
            title = args["title"]
            message = args["message"]
            urgency = args.get("urgency", "normal")
            # Try Termux first
            r = subprocess.run(["termux-notification", "--title", title, "--content", message], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return "Termux notification sent"
            # Try notify-send
            r = subprocess.run(["notify-send", "-u", urgency, title, message], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return "Desktop notification sent"
            return "Error: No notification system available (termux-notification or notify-send)"

        elif name == "bark_send":
            server = args.get("server") or os.environ.get("BARK_URL", "https://api.day.app")
            key = args.get("key") or os.environ.get("BARK_KEY", "")
            if not key:
                return "Error: BARK_KEY not set"
            title = args.get("title", "KEYZBOT")
            resp = requests.get(f"{server}/{key}/{title}/{args['message']}", timeout=10)
            return f"Bark notification sent (HTTP {resp.status_code})"

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error: {e}"
