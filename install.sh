#!/usr/bin/env bash
# Installer for oura-mcp — creates venv, installs deps, guides token setup.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TOKEN_DIR="$HOME/.config/oura-mcp"
TOKEN_PATH="$TOKEN_DIR/token"

echo "──────────────────────────────────────────────────"
echo "  oura-mcp installer"
echo "──────────────────────────────────────────────────"

# 1. Token setup
if [ -z "${OURA_TOKEN:-}" ] && [ ! -f "$TOKEN_PATH" ]; then
  echo ""
  echo "  Oura token not found."
  echo ""
  echo "  Get your Personal Access Token from:"
  echo "  https://cloud.ouraring.com/personal-access-tokens"
  echo ""
  read -rp "  Paste your token here (or press Enter to skip): " USER_TOKEN
  if [ -n "$USER_TOKEN" ]; then
    mkdir -p "$TOKEN_DIR"
    echo "$USER_TOKEN" > "$TOKEN_PATH"
    chmod 600 "$TOKEN_PATH"
    echo "  ✓ Token saved to $TOKEN_PATH"
  else
    echo "  Skipped. Set OURA_TOKEN env var or create $TOKEN_PATH later."
  fi
else
  echo "  ✓ Token found"
fi

# 2. Venv
if [ ! -d "$VENV" ]; then
  echo "  Creating venv at $VENV ..."
  "$PYTHON_BIN" -m venv "$VENV"
fi

echo "  Installing dependencies ..."
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet "mcp>=1.27.0"

# 3. Smoke test
echo "  Smoke-testing ..."
"$VENV/bin/python" -m py_compile "$HERE/client.py" "$HERE/server.py"

# 4. Print config snippet
cat <<EOF

──────────────────────────────────────────────────
  ✓ Install complete.
──────────────────────────────────────────────────

  Add this to your Claude Desktop config
  (~/Library/Application Support/Claude/claude_desktop_config.json)
  under "mcpServers":

  "oura": {
    "command": "$VENV/bin/python",
    "args": ["$HERE/server.py"]
  }

  For Claude Code, add to .claude/settings.json:

  "mcpServers": {
    "oura": {
      "command": "$VENV/bin/python",
      "args": ["$HERE/server.py"]
    }
  }

  Then restart Claude and try: "How did I sleep last night?"
──────────────────────────────────────────────────
EOF
