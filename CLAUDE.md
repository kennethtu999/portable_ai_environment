# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A portable, self-bootstrapping AI environment that lets Windows (and macOS) users run Claude Code without manually installing Python or Node.js. Users download three ZIPs, drop them in a folder, and double-click an entry point. Everything else is automated.

Target audience: corporate users who connect to Claude via a custom API gateway (Anthropic-compatible) and cannot use the public Anthropic API directly.

## Developer Commands

Build the distributable app ZIP (output: `dist/portable_claude_env.zip`):
```bash
./dev/build_zip.sh
```

Prepare all three ZIPs for distribution (app + WinPython + Node.js):
```bash
./dev/prepare_all_zip.sh
```

Test the macOS entry point locally:
```bash
chmod +x app/panel.command && ./app/panel.command
```

Test individual scripts directly (requires `.venv` already set up):
```bash
app/.venv/bin/python app/scripts/health_markitdown.py
app/.venv/bin/python app/scripts/health_claude.py
```

## Architecture

### Delivery Model

Users receive 3 files placed in the same folder:
- `portable_claude_env.zip` — the main app (contents of `app/`)
- `WinPython64-*.zip` — portable Python for Windows (no system install needed)
- `node-v*-win-x64.zip` — portable Node.js for Windows (Claude CLI depends on it)

On macOS, only `portable_claude_env.zip` is needed; system Python is used.

### Entry Point Flow (`init.bat` / `panel.command`)

Both entry points share identical logic:

1. **First run only** — Extract WinPython/Node.js ZIPs (auto-download if not present), create `.venv`, install `requirements.txt`, run MarkItDown health check (`scripts/health_markitdown.py`), then delete sample docs from `test_docs/`
2. **Every run** — Run `scripts/setup_env.py` (interactive first time, skips if already configured), run `scripts/health_claude.py`, verify Claude CLI is installed. Exit after setup — use `cc.bat` to launch Claude.

First-run detection: presence of `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (macOS).

### Scripts

| Script | Purpose |
|---|---|
| `setup_env.py` | Interactive wizard saving connection config to `~/.portable-markitdown-claude/claude.env`. Skips if already configured. CI mode: reads from env vars. |
| `health_markitdown.py` | Converts `test_docs/sample.{docx,xlsx,pdf}` to markdown to verify MarkItDown install. |
| `health_claude.py` | Sends `"reply OK"` to Claude API (starts proxy if needed) to verify connectivity. |
| `proxy.py` | Local HTTP proxy that rewrites requests before forwarding to the target API gateway. |
| `launch_claude.py` | Loads `claude.env`, optionally starts `proxy.py`, then exec's `claude` CLI. |

### Local Proxy (`proxy.py`)

The proxy rewrites outbound requests to handle target endpoint compatibility:
- **Model name mapping**: full versioned IDs (e.g. `claude-haiku-4-5-20251001`) → short IDs (`claude-haiku-4-5`) via `MODEL_MAPPING` dict
- **Strips unsupported params**: `top_p: -1`, `top_k: -1`, `context_management`
- Supports SSE streaming (byte-by-byte passthrough)
- Runs at `localhost:8888` by default (`PROXY_PORT`)

### Configuration File

Stored at `~/.portable-markitdown-claude/claude.env`. Contains:
- `ANTHROPIC_AUTH_TOKEN` — the API token
- `ANTHROPIC_BASE_URL` — either `http://127.0.0.1:{port}/v1` (proxy mode) or `https://{host}/v1` (direct mode)
- `PROXY_TARGET_HOST`, `PROXY_PORT` — proxy routing config
- `CLAUDE_MODEL` — model ID passed to the health check

`launch_claude.py` maps `ANTHROPIC_AUTH_TOKEN` → `ANTHROPIC_API_KEY` before invoking the Claude CLI (the CLI only accepts `ANTHROPIC_API_KEY`).

### Two Connection Modes

- **Via local proxy** (`choice=1`): `ANTHROPIC_BASE_URL` points to `localhost`; `proxy.py` is started by `launch_claude.py` and `health_claude.py`, forwarding requests to the target gateway over HTTPS
- **Direct** (`choice=2`): `ANTHROPIC_BASE_URL` points directly to the gateway host; no proxy process

### `app/` vs `dist/`

`app/` is the source of truth for what users receive. `dist/` is gitignored and holds build artifacts. `build_zip.sh` packages `app/` (excluding `.venv/`, `output/`, `__pycache__/`, `python/`, `node/`, `.zip` files, and `.env`) into `dist/portable_claude_env.zip`.

When updating `prepare_all_zip.sh`, version strings for WinPython and Node.js are in the `VERSION CONFIG` block at the top of the file. Same block exists in `init.bat` for the auto-download URLs.
