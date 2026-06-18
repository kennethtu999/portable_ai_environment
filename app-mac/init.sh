#!/bin/bash
set -e
AIENV_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$AIENV_DIR"

# ── VERSION CONFIG ────────────────────────────────────────────────────────────
NODE_VERSION="v24.16.0"
# ─────────────────────────────────────────────────────────────────────────────

# Detect arch for portable Node download fallback
ARCH=$(uname -m)
NODE_ARCH=$([ "$ARCH" = "arm64" ] && echo "darwin-arm64" || echo "darwin-x64")
NODE_FILE="node-${NODE_VERSION}-${NODE_ARCH}.tar.gz"
NODE_URL="https://nodejs.org/dist/${NODE_VERSION}/${NODE_FILE}"

# ── Step 1: Python (system >= 3.10 preferred, else brew fallback) ─────────────
PYTHON_CMD=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    if [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 10 ] 2>/dev/null; then
      PYTHON_CMD="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  if command -v brew &>/dev/null; then
    echo "[setup] Python 3.10+ not found. Installing via brew..."
    brew install python3
    PYTHON_CMD=python3
  else
    echo "[error] Python 3.10+ not found and brew is not available."
    echo "[info]  Install Python from https://www.python.org/ or brew from https://brew.sh"
    exit 1
  fi
fi
echo "[setup] Python: $($PYTHON_CMD --version) (system)"

# ── Step 2: Node.js (system >= 24 preferred, else portable fallback) ──────────
NODE_MARKER="tools/node/.installed-${NODE_FILE}"
_use_system_node=false
if command -v node &>/dev/null; then
  _node_major=$(node --version 2>/dev/null | grep -oE '[0-9]+' | head -1)
  if [ "${_node_major:-0}" -ge 24 ]; then
    _use_system_node=true
  fi
fi

if [ "$_use_system_node" = true ]; then
  echo "[setup] Node.js: $(node --version) (system)"
else
  if [ ! -f "$NODE_MARKER" ]; then
    if [ ! -f "$NODE_FILE" ]; then
      echo "[setup] Node.js not found or < 24. Downloading ${NODE_FILE}..."
      curl -L --progress-bar -o "$NODE_FILE" "$NODE_URL"
    fi
    echo "[setup] Extracting Node.js..."
    rm -rf tools/node
    mkdir -p tools/node
    tar -xf "$NODE_FILE" -C tools/node --strip-components=1
    touch "$NODE_MARKER"
  fi
  export PATH="$AIENV_DIR/tools/node/bin:$PATH"
  echo "[setup] Node.js: $(node --version) (portable)"
fi

# ── Step 3: brew tools (git, ripgrep, jq) ────────────────────────────────────
if command -v brew &>/dev/null; then
  for pkg in git ripgrep jq; do
    cmd=$([ "$pkg" = "ripgrep" ] && echo "rg" || echo "$pkg")
    if ! command -v "$cmd" &>/dev/null; then
      echo "[setup] Installing $pkg via brew..."
      brew install "$pkg"
    fi
  done
else
  for cmd in git rg jq; do
    command -v "$cmd" &>/dev/null || echo "[warn] $cmd not found. Install brew (https://brew.sh) or install manually."
  done
fi

# ── Step 4: Python venv ───────────────────────────────────────────────────────
if [ ! -f ".venv/bin/python" ]; then
  echo "[setup] Creating Python virtual environment..."
  "$PYTHON_CMD" -m venv .venv
  echo "[setup] Installing packages..."
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt
fi

# ── Step 5: API key setup (skips if already configured) ──────────────────────
echo "[env] Checking API key..."
.venv/bin/python scripts/setup_env.py

# ── Step 6: Claude API health check ──────────────────────────────────────────
echo "[health] Running Claude health check..."
.venv/bin/python scripts/health_claude.py

# ── Step 7: Claude CLI (local, no -g) ────────────────────────────────────────
# Add local npm-global to PATH so command -v can find a previously local-installed claude
export PATH="$AIENV_DIR/tools/npm-global/node_modules/.bin:$PATH"
if ! command -v claude &>/dev/null; then
  echo "[setup] Installing Claude CLI..."
  mkdir -p "$AIENV_DIR/tools/npm-global"
  cd "$AIENV_DIR/tools/npm-global"
  npm install @anthropic-ai/claude-code
  cd "$AIENV_DIR"
fi

echo ""
echo "[done] Environment ready. Run ai-env/cc.sh from your project folder."
