#!/usr/bin/env bash
# 用途：使用 dist/ 中的 ZIP 在乾淨 Podman 容器中驗證完整 bootstrap 流程
#
# ZIP 來源（與實際交付使用者的檔案相同）：
#   ZIP 1: dist/portable_claude_env.zip  — 主程式（不存在時自動呼叫 build_zip.sh）
#   ZIP 2: python-build-standalone       — Python 提供者（Linux 版，對應 WinPython）
#   ZIP 3: Node.js Linux                 — Node.js 執行環境
#
# 使用方式：
#   ./dev/validate_podman.sh                               # 驗證環境安裝
#   ANTHROPIC_API_KEY=sk-ant-xxx ./dev/validate_podman.sh  # 同時驗證 Claude API
#   ./dev/validate_podman.sh /path/to/app.zip              # 指定外部 app ZIP

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_DIR/dist"
CACHE_DIR="$HOME/.portable-markitdown-claude"
CID=""

# ── VERSION CONFIG ─────────────────────────────────────────────────────────────
PYTHON_BUNDLE_URL="https://github.com/indygreg/python-build-standalone/releases/download/20250529/cpython-3.11.12+20250529-aarch64-unknown-linux-gnu-install_only_stripped.tar.gz"
NODE_VERSION="v24.16.0"
NODE_BUNDLE_URL="https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-linux-arm64.tar.gz"
# ──────────────────────────────────────────────────────────────────────────────

APP_ZIP="${1:-}"

cleanup() {
  [ -n "$CID" ] && podman rm -f "$CID" &>/dev/null || true
}
trap cleanup EXIT

# ── Podman 準備 ────────────────────────────────────────────────────────────────
if ! command -v podman &>/dev/null; then
  echo "[error] Podman not found. Install: https://podman.io/getting-started/installation"
  exit 1
fi
if podman machine list &>/dev/null 2>&1; then
  if ! podman machine list 2>/dev/null | grep -q "Currently running"; then
    echo "[info] Starting podman machine..."
    podman machine start 2>/dev/null || true
    sleep 3
  fi
fi

# ── ZIP 1: App ZIP ─────────────────────────────────────────────────────────────
if [ -z "$APP_ZIP" ]; then
  APP_ZIP="$DIST_DIR/portable_claude_env.zip"
  if [ ! -f "$APP_ZIP" ]; then
    echo "[validate] dist/portable_claude_env.zip not found — building..."
    bash "$SCRIPT_DIR/build_zip.sh"
  fi
fi
[ ! -f "$APP_ZIP" ] && echo "[error] App ZIP not found: $APP_ZIP" && exit 1
echo "[validate] ZIP 1 (app): $(basename "$APP_ZIP") ($(du -sh "$APP_ZIP" | cut -f1))"

# ── ZIP 2 & 3: Linux bundle（快取）─────────────────────────────────────────────
PYTHON_BUNDLE="$CACHE_DIR/python-bundle-linux.tar.gz"
NODE_BUNDLE="$CACHE_DIR/node-bundle-linux-${NODE_VERSION}.tar.gz"
mkdir -p "$CACHE_DIR"

_dl() {
  local label="$1" url="$2" dest="$3"
  if [ ! -f "$dest" ]; then
    echo "[validate] $label: Downloading (one-time)..."
    if command -v curl &>/dev/null; then
      curl -L --progress-bar -o "$dest" "$url"
    else
      wget -q --show-progress -O "$dest" "$url"
    fi
  else
    echo "[validate] $label: Using cached bundle."
  fi
}

_dl "ZIP 2 (Python bundle)" "$PYTHON_BUNDLE_URL" "$PYTHON_BUNDLE"
_dl "ZIP 3 (Node.js bundle)" "$NODE_BUNDLE_URL"  "$NODE_BUNDLE"

# ── 啟動容器，複製 ZIPs ────────────────────────────────────────────────────────
IMAGE="debian:12-slim"
echo "[validate] Pulling image: $IMAGE (no Python pre-installed)"
podman pull "$IMAGE" --quiet

echo "[validate] Starting clean container..."
CID=$(podman run -d "$IMAGE" sleep 600)

echo "[validate] Copying 3 ZIPs to container..."
podman cp "$APP_ZIP"       "$CID:/tmp/portable_claude_env.zip"
podman cp "$PYTHON_BUNDLE" "$CID:/tmp/python-bundle.tar.gz"
podman cp "$NODE_BUNDLE"   "$CID:/tmp/node-bundle.tar.gz"

[ -z "${ANTHROPIC_API_KEY:-}" ] && echo "[validate] ANTHROPIC_API_KEY not set — skipping Claude health check."
echo ""

# ── Bootstrap 驗證 ────────────────────────────────────────────────────────────
podman exec "$CID" bash -c "
  set -e
  apt-get update -qq && apt-get install -y unzip -qq 2>/dev/null

  echo '[container] ZIP 2: Extracting Python bundle...'
  mkdir -p /opt/python
  tar -xf /tmp/python-bundle.tar.gz -C /opt/python
  PYTHON_BIN=\$(find /opt/python -name 'python3.11' -not -type d | head -1)
  echo \"[container] Python: \$PYTHON_BIN (\$(\"\$PYTHON_BIN\" --version 2>&1))\"

  echo '[container] ZIP 3: Extracting Node.js bundle...'
  mkdir -p /opt/node
  tar -xf /tmp/node-bundle.tar.gz -C /opt/node --strip-components=1
  export PATH=/opt/node/bin:\$PATH
  echo \"[container] Node: \$(node --version), npm: \$(npm --version)\"

  echo '[container] ZIP 1: Extracting app...'
  mkdir -p /tmp/app && cd /tmp/app
  unzip -q /tmp/portable_claude_env.zip

  echo '[container] Step a: Creating venv...'
  \"\$PYTHON_BIN\" -m venv .venv
  echo '[container] Step a: Installing packages...'
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt -q

  echo '[container] Step b: MarkItDown health check...'
  .venv/bin/python scripts/health_markitdown.py
  rm -f test_docs/sample.docx test_docs/sample.xlsx test_docs/sample.pdf
  [ ! -f test_docs/sample.docx ] && echo '[container] Sample docs removed: OK'
  echo '[container] Steps a+b passed.'
"

# Step c+d: API key 用 -e 注入
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "[validate] Running Step c+d: Claude setup and health check..."
  podman exec -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$CID" bash -c "
    set -e
    cd /tmp/app
    echo '[container] Step c: Setup Claude API key...'
    .venv/bin/python scripts/setup_env.py
    echo '[container] Step d: Claude health check...'
    .venv/bin/python scripts/health_claude.py
  "
fi

echo ""
echo "[validate] Done. Bootstrap validated from dist/ ZIPs in clean Podman container."
echo "[validate] All checks passed."
