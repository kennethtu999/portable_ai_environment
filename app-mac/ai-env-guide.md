# AI Environment Guide (macOS)

This file is for AI assistants (Claude) to understand the tools available in this environment.

## Directory Layout

```
<project-root>/               ← Working directory (where you operate)
└── ai-env/                   ← This environment; all tools are under here
    ├── ai-env-guide.md       ← This file
    ├── tools/
    │   └── node/             ← Portable Node.js (fallback if system node absent)
    ├── .venv/                ← Python venv (internal use only)
    └── scripts/              ← Setup and health check scripts
```

The terminal's working directory is the **project root** (parent of `ai-env/`).  
All commands run relative to that folder.

## Tools in PATH

After `ai-env/cc.sh` is launched, the following commands are available:

| Command  | Description                | Source                          |
|----------|----------------------------|---------------------------------|
| `git`    | Git                        | system / brew                   |
| `node`   | Node.js runtime            | system / `tools/node/bin/node`  |
| `npm`    | Node package manager       | system / `tools/node/bin/npm`   |
| `claude` | Claude Code CLI            | `tools/npm-global/node_modules/.bin/claude` |
| `rg`     | ripgrep — fast file search | system / brew                   |
| `jq`     | JSON processor             | system / brew                   |

## Claude CLI

Claude is installed locally under `ai-env/tools/npm-global/`:

```bash
cd ai-env/tools/npm-global
npm install @anthropic-ai/claude-code
```

`cc.sh` adds `tools/npm-global/node_modules/.bin` to PATH automatically.  
If Claude is not found, `cc.sh` installs it automatically on first run.

## Python Environment

The `.venv` is for internal use by `init.sh` scripts (health checks, API key setup).  
It is **not** added to PATH. To invoke Python directly:

```bash
ai-env/.venv/bin/python <script>
```

## Tool Priority

| Tool   | Primary          | Fallback                    |
|--------|------------------|-----------------------------|
| Python | system python3   | `brew install python3`      |
| Node   | system node      | portable `tools/node/`      |
| git    | system git       | `brew install git`          |
| rg     | system rg        | `brew install ripgrep`      |
| jq     | system jq        | `brew install jq`           |

## Document Conversion

Convert documents (docx, xlsx, pdf, pptx, html, csv) to Markdown:

```bash
ai-env/.venv/bin/python ai-env/scripts/convert_docs.py <file_or_dir>
```

| Behaviour | Detail |
|-----------|--------|
| Output | `md-doc/` under project root |
| Images | Extracted as separate files in `md-doc/<stem>/` |
| Skip | Files with unchanged hash are skipped automatically |
| State | `ai-env/ai-state/convert_state.json` |
| Chunking | Files > 100 KB split by chapter headings; fallback to size |

## Version Upgrades

To upgrade portable Node.js, update `NODE_VERSION` in `ai-env/init.sh` and re-run it.
