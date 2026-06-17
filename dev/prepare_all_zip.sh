#!/usr/bin/env bash
# 用途：一次準備使用者需要的所有 ZIP，輸出到 dist/
#
# 輸出：
#   dist/portable_claude_env.zip   — 主程式
#   dist/WinPython64-X.X.X.Xdot.zip  — Python 環境（Windows 使用者）
#   dist/node-vX.X.X-win-x64.zip   — Node.js（Claude CLI 安裝用）
#
# 使用方式：./dev/prepare_all_zip.sh
# 更新版本：修改下方 VERSION 區塊

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/dist"
mkdir -p "$DIST_DIR"

# ── VERSION CONFIG ────────────────────────────────────────────────────────────
# WinPython dot (minimal, no extra packages) — https://github.com/winpython/winpython/releases
WINPYTHON_TAG="17.4.20260511final"
WINPYTHON_FILE="WinPython64-3.13.13.0dot.zip"

# Node.js Windows x64 — https://nodejs.org/en/download
NODE_VERSION="v24.16.0"
NODE_FILE="node-${NODE_VERSION}-win-x64.zip"
# ─────────────────────────────────────────────────────────────────────────────

WINPYTHON_URL="https://github.com/winpython/winpython/releases/download/${WINPYTHON_TAG}/${WINPYTHON_FILE}"
NODE_URL="https://nodejs.org/dist/${NODE_VERSION}/${NODE_FILE}"

_download() {
  local label="$1" url="$2" dest="$3"
  if [ -f "$dest" ]; then
    echo "[prepare] $label: already exists, skipping."
    return
  fi
  echo "[prepare] $label: Downloading..."
  if command -v curl &>/dev/null; then
    curl -L --progress-bar -o "$dest" "$url"
  elif command -v wget &>/dev/null; then
    wget -q --show-progress -O "$dest" "$url"
  else
    echo "[error] curl or wget required."
    exit 1
  fi
  echo "[prepare] $label: $(du -sh "$dest" | cut -f1)"
}

echo "============================================================"
echo " prepare_all_zip — building dist/ for distribution"
echo "============================================================"

# 1. App ZIP
echo ""
echo "[prepare] Step 1/3: Building app ZIP..."
bash "$SCRIPT_DIR/build_zip.sh"

# 2. WinPython
echo ""
echo "[prepare] Step 2/3: WinPython (Python environment)..."
_download "WinPython" "$WINPYTHON_URL" "$DIST_DIR/$WINPYTHON_FILE"

# 3. Node.js Windows
echo ""
echo "[prepare] Step 3/3: Node.js Windows..."
_download "Node.js" "$NODE_URL" "$DIST_DIR/$NODE_FILE"

echo ""
echo "============================================================"
echo " Done. Files in dist/:"
ls -lh "$DIST_DIR"
echo ""
echo " Distribute these 3 files to Windows users (same folder):"
echo "   portable_claude_env.zip"
echo "   $WINPYTHON_FILE"
echo "   $NODE_FILE"
echo "============================================================"
