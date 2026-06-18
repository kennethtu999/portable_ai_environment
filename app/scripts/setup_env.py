from pathlib import Path
import json
import os

APP_DIR = Path.home() / ".portable_ai_environment"
ENV_FILE = APP_DIR / "claude.env"

APP_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL       = "claude-sonnet-4-6"
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
    # No path suffix — Anthropic SDK appends /v1/messages itself
    base_url = f"http://127.0.0.1:{port}"
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
        f'CLAUDE_MODEL="{model}"\n'
        f"\n"
        f"# ── Optional: ffmpeg for audio/video conversion ────────────────\n"
        f"# FFMPEG_PATH=\"C:\\path\\to\\ffmpeg\\bin\"\n",
        encoding="utf-8",
    )
    print(f"[env] Saved to: {ENV_FILE}")


def _write_direct(token: str, host: str, model: str) -> None:
    # Accept bare host, host/path, or full URL — SDK appends /v1/messages itself
    base_url = host if "://" in host else f"https://{host}"
    base_url = base_url.rstrip("/")
    ENV_FILE.write_text(
        f"# ── Connection ────────────────────────────────────────────────\n"
        f'ANTHROPIC_AUTH_TOKEN="{token}"\n'
        f'ANTHROPIC_BASE_URL="{base_url}"\n'
        f"\n"
        f"# ── Target ─────────────────────────────────────────────────────\n"
        f'PROXY_TARGET_HOST="{host}"\n'
        f"\n"
        f"# ── Model ─────────────────────────────────────────────────────\n"
        f'CLAUDE_MODEL="{model}"\n'
        f"\n"
        f"# ── Claude Code compatibility ──────────────────────────────────\n"
        f"# Disable experimental betas unsupported by custom API gateways\n"
        f"CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1\n"
        f"\n"
        f"# ── Optional: ffmpeg for audio/video conversion ────────────────\n"
        f"# FFMPEG_PATH=\"C:\\path\\to\\ffmpeg\\bin\"\n",
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

token = input("Enter API token: ").strip()
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

# Set default Claude Code model — only in CI mode (env vars set).
# Interactive installs skip this: model availability depends on the gateway,
# so let users pick via /model after first launch.
if env_auth_token and env_base_url:
    _claude_settings = Path.home() / ".claude" / "settings.json"
    _claude_settings.parent.mkdir(parents=True, exist_ok=True)
    _settings = {}
    if _claude_settings.exists():
        try:
            _settings = json.loads(_claude_settings.read_text(encoding="utf-8"))
        except Exception:
            pass
    if "model" not in _settings:
        _settings["model"] = "claude-sonnet-4-6[1m]"
        _claude_settings.write_text(json.dumps(_settings, indent=2), encoding="utf-8")
        print("[env] Default Claude model set: claude-sonnet-4-6[1m]")
