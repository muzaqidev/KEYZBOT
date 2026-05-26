"""UI rendering for KEYZBOT."""

import os, sys, re, shutil, textwrap, threading, time

# ─── Style ────────────────────────────────────────────────────────────────────
class S:
    R    = "\033[0m"
    B    = "\033[1m"
    D    = "\033[2m"
    I    = "\033[3m"
    U    = "\033[4m"
    RED  = "\033[31m"
    GRN  = "\033[32m"
    YLW  = "\033[33m"
    BLU  = "\033[34m"
    MAG  = "\033[35m"
    CYN  = "\033[36m"
    WHT  = "\033[37m"
    BRED = "\033[91m"
    BGRN = "\033[92m"
    BYLW = "\033[93m"
    BBLU = "\033[94m"
    BMAG = "\033[95m"
    BCYN = "\033[96m"
    BWHT = "\033[97m"
    BG_BBLK = "\033[100m"

# ─── Terminal ─────────────────────────────────────────────────────────────────
def width():
    try: return shutil.get_terminal_size().columns
    except Exception: return 60

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def hide_cur():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cur():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def vis_len(text):
    return len(re.sub(r'\033\[[0-9;]*m', '', text))

# ─── Markdown Renderer ────────────────────────────────────────────────────────
def render_md(text, indent="    "):
    """Render markdown to ANSI-colored lines."""
    lines = text.split("\n")
    out = []
    in_code = False

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                out.append(f"{indent}{S.D}{'─' * 50}{S.R}")
                in_code = False
            else:
                in_code = True
                out.append(f"{indent}{S.D}{'─' * 50}{S.R}")
            continue

        if in_code:
            out.append(f"{indent}{S.BG_BBLK}{S.BWHT} {line} {S.R}")
            continue

        if line.startswith("#### "):
            out.append(f"{indent}{S.B}{S.BYLW}{line[5:]}{S.R}")
            continue
        if line.startswith("### "):
            out.append(f"{indent}{S.B}{S.BYLW}{line[4:]}{S.R}")
            continue
        if line.startswith("## "):
            out.append(f"{indent}{S.B}{S.BCYN}{line[3:]}{S.R}")
            continue
        if line.startswith("# "):
            out.append(f"{indent}{S.B}{S.BMAG}{line[2:]}{S.R}")
            continue

        if re.match(r'^[\-\*]\s', line.strip()):
            content = re.sub(r'^[\-\*]\s', '', line.strip())
            rendered = _inline(content)
            out.append(f"{indent}{S.BCYN}▸{S.R} {rendered}")
            continue

        m = re.match(r'^(\d+)\.\s', line.strip())
        if m:
            num = m.group(1)
            rest = line.strip()[m.end():]
            rendered = _inline(rest)
            out.append(f"{indent}{S.BCYN}{num}.{S.R} {rendered}")
            continue

        if line.strip() == "":
            out.append("")
            continue

        out.append(f"{indent}{_inline(line)}")

    return out

def _inline(text):
    """Render inline markdown."""
    text = re.sub(r'\*\*(.+?)\*\*', f'{S.B}{S.BWHT}\\1{S.R}', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', f'{S.I}\\1{S.R}', text)
    text = re.sub(r'`(.+?)`', f'{S.BG_BBLK}{S.BWHT} \\1 {S.R}', text)
    return text

# ─── Thinking Animation ──────────────────────────────────────────────────────
class Spinner:
    def __init__(self, label="Thinking"):
        self._stop = threading.Event()
        self._thread = None
        self.label = label
        self._frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        i = 0
        while not self._stop.is_set():
            f = self._frames[i % len(self._frames)]
            dots = "." * ((i // 4) % 4)
            sys.stdout.write(f"\r\033[K  {S.BMAG}{f}{S.R} {S.D}{self.label}{dots}{S.R}  ")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)
        clear_line()

# ─── Banner ───────────────────────────────────────────────────────────────────
def banner(cfg):
    clear()
    w = width()

    art = [
        "  ██╗  ██╗███████╗██╗   ██╗ ███████╗██████╗  ██████╗ ████████╗",
        "  ██║ ██╔╝╚══███╔╝╚██╗ ██╔╝╚══███╔╝██╔══██╗ ██╔══██╗╚══██╔══╝",
        "  ██████╔╝   ███╔╝  ╚████╔╝   ███╔╝  ██████╔╝ ██████╔╝   ██║",
        "  ██╔═██╗   ███╔╝    ╚██╔╝   ███╔╝  ██╔══██╗ ██╔══██╗   ██║",
        "  ██║  ██╗ ███████╗   ██║   ███████╗██████╔╝ ██████╔╝   ██║",
        "  ╚═╝  ╚═╝ ╚══════╝   ╚═╝   ╚══════╝╚═════╝  ╚═════╝    ╚═╝",
    ]

    print()
    print(f"  {S.BCYN}{'━' * (w - 4)}{S.R}")
    print()
    for l in art:
        print(f"  {S.BCYN}{S.B}{l}{S.R}")
    print()
    print(f"  {S.BCYN}{'━' * (w - 4)}{S.R}")
    print()

    info = [
        ("Model", cfg["model"]),
        ("Temp",  str(cfg["temperature"])),
        ("Tokens", str(cfg["max_tokens"])),
    ]
    for label, val in info:
        print(f"  {S.D}{label:>10}{S.R}  {S.BWHT}{val}{S.R}")

    print()
    print(f"  {S.D}Type {S.BCYN}/help{S.R}{S.D} for commands  |  {S.BCYN}/exit{S.R}{S.D} to quit{S.R}")
    print(f"  {S.D}v7.0 — Full AI Agent: 15 tools, memory, plans, tasks, agents, skills{S.R}")
    print(f"  {S.BCYN}{'━' * (w - 4)}{S.R}")
    print()

# ─── Setup ────────────────────────────────────────────────────────────────────
def setup():
    """First-time interactive setup."""
    from . import config as cfg_mod
    clear()
    w = width()
    print()
    print(f"  {S.BCYN}{'━' * (w - 4)}{S.R}")
    print(f"  {S.B}{S.BCYN}KEYZBOT{S.R}  {S.D}First Time Setup{S.R}")
    print(f"  {S.BCYN}{'━' * (w - 4)}{S.R}")
    print()

    det = cfg_mod.auto_detect()
    if det.get("api_key"):
        masked = det["api_key"][:12] + "..." + det["api_key"][-4:]
        print(f"  {S.BGRN}Auto-detected from OpenClaude:{S.R}")
        print(f"  {S.D}  Base URL  {S.R} {det['base_url']}")
        print(f"  {S.D}  Model     {S.R} {det['model']}")
        print(f"  {S.D}  API Key   {S.R} {masked}")
        print()
        u = input(f"  {S.BYLW}?{S.R} Use this config ({S.BGRN}Y{S.R}/n): ").strip().lower()
        if u != "n":
            cfg_mod.save(det)
            return det

    c = cfg_mod.DEFAULTS.copy()
    print(f"  {S.D}Manual setup:{S.R}\n")
    v = input(f"  {S.D}Base URL{S.R} [{S.D}{c['base_url']}{S.R}]: ").strip()
    if v: c["base_url"] = v
    v = input(f"  {S.D}Model{S.R} [{S.D}{c['model']}{S.R}]: ").strip()
    if v: c["model"] = v
    v = input(f"  {S.D}API Key{S.R}: ").strip()
    if v: c["api_key"] = v
    cfg_mod.save(c)
    print(f"\n  {S.BGRN}Saved!{S.R}\n")
    return c

# ─── Display helpers ──────────────────────────────────────────────────────────
def user_msg(text):
    w = width()
    print()
    print(f"  {S.BGRN}{S.B}You{S.R}")
    print(f"  {S.D}▸{S.R}")
    for wl in textwrap.wrap(text, width=w - 8, break_long_words=True):
        print(f"    {S.BWHT}{wl}{S.R}")

def bot_label():
    print(f"\n  {S.BMAG}{S.B}KEYZBOT{S.R}")
    print(f"  {S.D}▸{S.R}")

def bot_stream_line(text):
    """Print a single line of bot response during streaming."""
    indent = "    "
    rendered = _inline(text)
    vis = vis_len(text)
    w = width() - len(indent) - 2
    pad = max(0, w - vis)
    sys.stdout.write(f"\r\033[K{indent}{rendered}{' ' * pad}")
    sys.stdout.flush()

def bot_stream_newline():
    sys.stdout.write("\n")
    sys.stdout.flush()

def tool_display(name, args_str, result):
    """Display a tool call and its result."""
    w = width()
    print()
    print(f"  {S.BBLU}{S.B}{S.BG_BBLK} tool {S.R} {S.BBLU}{name}{S.R}")
    if args_str:
        # Truncate if too long
        if len(args_str) > 200:
            args_str = args_str[:200] + "..."
        print(f"  {S.D}{args_str}{S.R}")
    print(f"  {S.D}{'─' * min(w - 4, 50)}{S.R}")
    if result:
        # Show result (truncated)
        result_lines = result.strip().split("\n")
        max_lines = 20
        for line in result_lines[:max_lines]:
            # Truncate long lines
            if len(line) > w - 8:
                line = line[:w - 11] + "..."
            print(f"  {S.D}│{S.R} {line}")
        if len(result_lines) > max_lines:
            print(f"  {S.D}│{S.R} {S.D}... ({len(result_lines) - max_lines} more lines){S.R}")
    print()

def status_line(tokens, model):
    w = width()
    print(f"  {S.D}{'─' * (w - 4)}{S.R}")
    print(f"  {S.D}tokens: {tokens}  │  model: {model}{S.R}")
    print()

def cmd_box(title, lines):
    w = width()
    print()
    print(f"  {S.BCYN}{S.B}{title}{S.R}")
    print(f"  {S.BCYN}{'─' * (w - 4)}{S.R}")
    for l in lines:
        print(f"  {l}")
    print()

def error_box(msg):
    cmd_box("Error", [f"{S.BRED}{msg}{S.R}"])

def success_box(msg):
    cmd_box("Done", [f"{S.BGRN}{msg}{S.R}"])

def info_box(title, lines):
    cmd_box(title, lines)

def tool_permission(name, args_str, reason):
    """Show tool permission request."""
    print()
    print(f"  {S.BYLW}{S.B}?{S.R} {S.BBLU}{name}{S.R} needs permission")
    if args_str:
        print(f"  {S.D}{args_str}{S.R}")
    print(f"  {S.D}Reason: {reason}{S.R}")

def spinner_box(text):
    """Show a quick spinner for short operations."""
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i in range(6):
        f = frames[i % len(frames)]
        sys.stdout.write(f"\r\033[K  {S.BMAG}{f}{S.R} {S.D}{text}...{S.R}  ")
        sys.stdout.flush()
        time.sleep(0.08)
    clear_line()
