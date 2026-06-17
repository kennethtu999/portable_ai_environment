from pathlib import Path
import os
import subprocess
import sys
import time
from dotenv import load_dotenv
from anthropic import Anthropic

APP_DIR = Path.home() / ".portable-markitdown-claude"
ENV_FILE = APP_DIR / "claude.env"

if not ENV_FILE.exists():
    raise SystemExit(f"[error] Missing env file: {ENV_FILE}")

load_dotenv(ENV_FILE)

api_key  = os.getenv("ANTHROPIC_AUTH_TOKEN")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model    = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

if not api_key:
    raise SystemExit("[error] ANTHROPIC_AUTH_TOKEN is not set.")

# proxy 模式：health check 前先啟動 proxy，check 完再關掉
proxy_proc = None
if base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
    scripts_dir = Path(__file__).parent
    print(f"[claude] Starting proxy for health check ({base_url})...")
    proxy_proc = subprocess.Popen(
        [sys.executable, str(scripts_dir / "proxy.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    if proxy_proc.poll() is not None:
        err = proxy_proc.stderr.read().decode(errors="replace")
        raise SystemExit(f"[error] Proxy failed to start: {err}")

try:
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
        print(f"[claude] Using base URL: {base_url}")

    client = Anthropic(**client_kwargs)

    message = client.messages.create(
        model=model,
        max_tokens=20,
        messages=[{"role": "user", "content": "reply OK"}],
    )

    text = "".join(
        block.text for block in message.content
        if getattr(block, "type", None) == "text"
    )
    print(f"[claude] Response: {text.strip()}")

    if "OK" not in text.upper():
        raise SystemExit("[error] Claude health check failed.")

    print("[claude] Health check passed.")

finally:
    if proxy_proc:
        proxy_proc.terminate()
        proxy_proc.wait()
