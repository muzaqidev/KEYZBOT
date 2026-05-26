#!/bin/bash
# KEYZBOT Installer
echo -e "\033[96m\033[1m"
echo "  ╔══════════════════════════════════════╗"
echo "  ║      KEYZBOT - Installing...         ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="/usr/local/bin/keyzbot"

# Create launcher
cat > "$TARGET" << LAUNCHER
#!/bin/bash
exec python3 "$SCRIPT_DIR/keyzbot.py" "\$@"
LAUNCHER
chmod +x "$TARGET"
chmod +x "$SCRIPT_DIR/keyzbot.py"
chmod +x "$SCRIPT_DIR/keyzbot"

echo ""
echo -e "  \033[92mInstalled! Run: keyzbot\033[0m"
echo ""
