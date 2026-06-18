from pathlib import Path
import os
import getpass

APP_DIR  = Path.home() / ".portable-markitdown-claude"
ENV_FILE = APP_DIR / "claude.env"

APP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL       = "claude-haiku-4-5-20251001"
DEFAULT_PROXY_HOST  = ""
DEFAULT_PROXY_PORT  = "8888"


def _read_env() -> dict:
    result = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip().strip('"')
    return result


def _write_proxy(token: str, port: str, host: str, model: str) -> None:
    base_url = f"http://127.0.0.1:{port}/v1"
    ENV_FILE.write_text(
        f"# ── Connection ────────────────────────────────────────────────\n"
        f'ANTHROPIC_AUTH_TOKEN="{token}"\n'
        f'ANTHROPIC_BASE_URL="{base_url}"\n'
        f"\n"
        f"# ── Local Proxy ────────────────────────────────────────────────\n"
        f'PROXY_TARGET_HOST="{host}"\n'
        f'PROXY_PORT="{port}"\n'
        f"\n"
        f"# ── Model ─────────────────────────────────────────────────────\n"
        f'CLAUDE_MODEL="{model}"\n',
        encoding="utf-8",
    )
    print(f"[env] Saved to: {ENV_FILE}")


def _write_direct(token: str, host: str, model: str) -> None:
    base_url = f"https://{host}/v1"
    ENV_FILE.write_text(
        f"# ── Connection ────────────────────────────────────────────────\n"
        f'ANTHROPIC_AUTH_TOKEN="{token}"\n'
        f'ANTHROPIC_BASE_URL="{base_url}"\n'
        f"\n"
        f"# ── Target ─────────────────────────────────────────────────────\n"
        f'PROXY_TARGET_HOST="{host}"\n'
        f"\n"
        f"# ── Model ─────────────────────────────────────────────────────\n"
        f'CLAUDE_MODEL="{model}"\n',
        encoding="utf-8",
    )
    print(f"[env] Saved to: {ENV_FILE}")


existing = _read_env()

# CI/container: read from env vars, skip interactive
env_auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
env_base_url   = os.environ.get("ANTHROPIC_BASE_URL", "").strip()

if env_auth_token and env_base_url:
    if "127.0.0.1" in env_base_url or "localhost" in env_base_url:
        port = os.environ.get("PROXY_PORT", DEFAULT_PROXY_PORT)
        host = os.environ.get("PROXY_TARGET_HOST", DEFAULT_PROXY_HOST)
        _write_proxy(env_auth_token, port, host, os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL))
    else:
        host = os.environ.get("PROXY_TARGET_HOST", DEFAULT_PROXY_HOST)
        _write_direct(env_auth_token, host, os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL))
    raise SystemExit(0)

# Already configured
if existing.get("ANTHROPIC_AUTH_TOKEN") and existing.get("ANTHROPIC_BASE_URL"):
    print(f"[env] base_url={existing['ANTHROPIC_BASE_URL']}  (edit {ENV_FILE} to change)")
    raise SystemExit(0)

# Interactive setup
print()
print("[env] Select connection mode:")
print("  1. Via local proxy  (proxy runs at localhost)")
print("  2. Direct connection  (no local proxy)")
print()

choice = input("Choice [1]: ").strip() or "1"

token = getpass.getpass("Enter API token: ").strip()
if not token:
    raise SystemExit("[error] API token is required.")

if choice == "1":
    port_input = input(f"Proxy port [{DEFAULT_PROXY_PORT}]: ").strip() or DEFAULT_PROXY_PORT
    host_input = input(f"Gateway host [{DEFAULT_PROXY_HOST}]: ").strip() or DEFAULT_PROXY_HOST
    _write_proxy(token, port_input, host_input, DEFAULT_MODEL)
elif choice == "2":
    host_input = input(f"Gateway host [{DEFAULT_PROXY_HOST}]: ").strip() or DEFAULT_PROXY_HOST
    _write_direct(token, host_input, DEFAULT_MODEL)
else:
    raise SystemExit("[error] Invalid choice.")
