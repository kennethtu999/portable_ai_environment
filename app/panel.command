#!/bin/bash
set -e
cd "$(dirname "$0")"

# Step a: 第一次執行 — 建立 venv、安裝套件
if [ ! -f ".venv/bin/python" ]; then

  # 偵測同目錄下的 Node.js tarball (node-v*.tar.gz / node-v*.tar.xz)
  for f in node-v*.tar.gz node-v*.tar.xz; do
    [ -f "$f" ] || continue
    if [ ! -d "node" ]; then
      echo "[setup] Extracting Node.js from $f..."
      mkdir -p node
      tar -xf "$f" -C node --strip-components=1
    fi
    break
  done

  echo "[setup] Creating Python virtual environment..."
  python3 -m venv .venv

  echo "[setup] Installing required packages..."
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt

  # Step b: MarkItDown health check — convert docx/xlsx/pdf, then remove sample docs
  echo "[health] Running MarkItDown health check..."
  .venv/bin/python scripts/health_markitdown.py

  rm -f test_docs/sample.docx test_docs/sample.xlsx test_docs/sample.pdf
  echo "[health] Sample docs removed after health check."
fi

# Step c: Setup Claude API key (save to home folder, skip if already set)
echo "[env] Setting up Claude API key..."
.venv/bin/python scripts/setup_env.py

# Step d: Claude health check — single prompt 'reply OK'
echo "[health] Running Claude health check..."
.venv/bin/python scripts/health_claude.py

echo "[done] Environment is ready."

# Step e: 設定 PATH（bundled node 優先）、安裝 claude（若需要）、開啟 Claude
set +e
if [ -d "node/bin" ]; then
  export PATH="$(pwd)/node/bin:$PATH"
fi

if ! command -v claude &>/dev/null; then
  if command -v npm &>/dev/null; then
    echo "[setup] Installing Claude CLI via bundled npm..."
    npm install -g @anthropic-ai/claude-code
  fi
fi

source .venv/bin/activate
.venv/bin/python scripts/launch_claude.py
