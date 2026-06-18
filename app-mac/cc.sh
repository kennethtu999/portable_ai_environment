#!/bin/bash
# Run from your project folder: ai-env/cc.sh
# Claude opens with the current directory as its working directory.
AIENV_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$HOME/.portable_ai_environment/claude.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "[error] claude.env not found. Run ai-env/init.sh first."
  exit 1
fi

# Add portable node to PATH if system node not available
if ! command -v node &>/dev/null; then
  if [ -f "$AIENV_DIR/tools/node/bin/node" ]; then
    export PATH="$AIENV_DIR/tools/node/bin:$PATH"
  fi
fi

# Ensure brew tools are in PATH
if command -v brew &>/dev/null; then
  export PATH="$(brew --prefix)/bin:$PATH"
fi

# Claude installed locally under tools/npm-global/node_modules
export PATH="$AIENV_DIR/tools/npm-global/node_modules/.bin:$PATH"

# Show available tools
echo ""
echo "Portable AI Terminal Ready"
echo ""
for cmd in git node npm claude rg jq; do
  bin=$(command -v "$cmd" 2>/dev/null)
  if [ -n "$bin" ]; then
    ver=$("$cmd" --version 2>&1 | head -1)
    printf "  %-8s %s\n" "$cmd" "$ver"
  else
    printf "  %-8s (not found — run ai-env/init.sh)\n" "$cmd"
  fi
done
echo ""

# Load env
set -o allexport
# shellcheck disable=SC1090
source "$ENV_FILE"
set +o allexport

# Start proxy if needed
PROXY_PID=
if echo "${ANTHROPIC_BASE_URL:-}" | grep -qE "127\.0\.0\.1|localhost"; then
  echo "[proxy] Starting local proxy..."
  "$AIENV_DIR/.venv/bin/python" "$AIENV_DIR/scripts/proxy.py" &
  PROXY_PID=$!
  sleep 1.5
  if ! kill -0 $PROXY_PID 2>/dev/null; then
    echo "[error] Proxy failed to start."
    exit 1
  fi
  echo "[proxy] Proxy running at $ANTHROPIC_BASE_URL"
fi

# ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL already loaded from env file

# Auto-install Claude CLI if missing (local, no -g)
if ! command -v claude &>/dev/null; then
  echo "[setup] Claude CLI not found. Installing..."
  mkdir -p "$AIENV_DIR/tools/npm-global"
  cd "$AIENV_DIR/tools/npm-global"
  npm install @anthropic-ai/claude-code
  node node_modules/@anthropic-ai/claude-code/install.cjs
  cd - > /dev/null
  echo ""
fi

CLAUDE_BIN="$AIENV_DIR/tools/npm-global/node_modules/.bin/claude"
echo "[next] Opening Claude... (working dir: $(pwd))"
"$CLAUDE_BIN"

if [ -n "$PROXY_PID" ]; then
  echo "[proxy] Stopping proxy..."
  kill $PROXY_PID 2>/dev/null || true
fi
