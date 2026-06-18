"""
用途：載入 .env、依模式啟動 proxy（若需要）、然後開啟 Claude CLI
使用方式：由 cc.bat / cc.sh 呼叫，不直接執行
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path.home() / ".portable_ai_environment" / "claude.env"
SCRIPTS_DIR = Path(__file__).parent

if not ENV_FILE.exists():
    print("[error] claude.env not found. Run setup_env.py first.")
    sys.exit(1)

load_dotenv(ENV_FILE)

auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
base_url   = os.getenv("ANTHROPIC_BASE_URL", "")

# Start local proxy if proxy mode
proxy_proc = None
if "127.0.0.1" in base_url or "localhost" in base_url:
    print("[proxy] Starting local proxy...")
    proxy_proc = subprocess.Popen(
        [sys.executable, str(SCRIPTS_DIR / "proxy.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    if proxy_proc.poll() is not None:
        err = proxy_proc.stderr.read().decode(errors="replace")
        print(f"[error] Proxy failed to start: {err}")
        sys.exit(1)
    print(f"[proxy] Proxy running at {base_url}")

# Prepare env for Claude
env = os.environ.copy()

# Find claude binary
claude_path = shutil.which("claude")
if not claude_path:
    print("[info] Claude CLI not found.")
    print("[info] Option 1: Place node-v*.zip/tar.gz in this folder (portable Node.js).")
    print("[info] Option 2: Install Node.js from https://nodejs.org/ then:")
    print("[info]           npm install -g @anthropic-ai/claude-code")
    if proxy_proc:
        proxy_proc.terminate()
    sys.exit(0)

print("[next] Opening Claude...")
try:
    subprocess.run([claude_path], env=env)
finally:
    if proxy_proc:
        print("[proxy] Stopping proxy...")
        proxy_proc.terminate()
