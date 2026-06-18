# AI Environment Guide

This file is for AI assistants (Claude) to understand the tools available in this environment.

## Directory Layout

```
<project-root>/               ← Working directory (where you operate)
└── ai-env/                   ← This environment; all tools are under here
    ├── ai-env-guide.md       ← This file
    ├── tools/
    │   ├── git/cmd/          ← MinGit  → git.exe
    │   ├── node/             ← Node.js → node.exe, npm.cmd
    │   ├── npm-global/       ← npm global packages → claude.cmd, etc.
    │   ├── rg/               ← ripgrep → rg.exe
    │   └── jq/               ← jq      → jq.exe
    ├── .venv/                ← Python venv (internal use only)
    └── scripts/              ← Setup and health check scripts
```

The terminal's working directory is the **project root** (parent of `ai-env\`).  
All `git`, `node`, `rg`, `jq`, `claude` commands run relative to that folder.

## Tools in PATH

After `cc.bat` is launched, the following commands are available:

| Command  | Description                          | Base path in ai-env           |
|----------|--------------------------------------|-------------------------------|
| `git`    | MinGit — portable Git                | `tools\git\cmd\git.exe`       |
| `node`   | Node.js runtime                      | `tools\node\node.exe`         |
| `npm`    | Node package manager                 | `tools\node\npm.cmd`          |
| `claude` | Claude Code CLI                      | `tools\npm-global\claude.cmd` |
| `rg`     | ripgrep — fast file search           | `tools\rg\rg.exe`             |
| `jq`     | JSON processor                       | `tools\jq\jq.exe`             |

## npm Global Packages

npm is configured to install global packages into `ai-env\tools\npm-global\`  
(not the Windows system directory). This keeps the environment self-contained.

```powershell
npm install -g <package>        # installs to ai-env\tools\npm-global\
```

The environment variable `NPM_CONFIG_PREFIX` is set automatically by `cc.bat`.

## Python Environment

The `.venv` is used internally by `init.bat` scripts (health checks, API key setup).  
It is **not** added to PATH. To invoke Python directly:

```powershell
ai-env\.venv\Scripts\python.exe <script>
```

## New Project Scaffold

Initialize AI collaboration docs for a new project (run once per project):

```powershell
ai-env\new-project.bat
# or with custom project path:
ai-env\new-project.bat C:\path\to\project
# overwrite existing files:
ai-env\new-project.bat --force
```

Creates in project root:

```
AGENTS.md                       <- collaboration rules (Codex / Cursor / Claude)
CLAUDE.md                       <- technical context + @AGENTS.md
ai-doc/
  MEMORY.md                     <- Claude knowledge index
  topic/
    topic_writing_rule.md
```

## Document Conversion

Convert documents (docx, xlsx, pdf, pptx, html, csv) to Markdown:

```powershell
ai-env\.venv\Scripts\python.exe ai-env\scripts\convert_docs.py <file_or_dir>
```

| Behaviour | Detail |
|-----------|--------|
| Output | `md-doc/` under project root |
| Images | Extracted as separate files in `md-doc/<stem>/` |
| Skip | Files with unchanged hash are skipped automatically |
| State | `ai-env/ai-state/convert_state.json` |
| Chunking | Files > 100 KB split by chapter headings; fallback to size |

## Version Upgrades

To upgrade any tool, update the version number in the `VERSION CONFIG` block  
at the top of `ai-env\init.bat`, then re-run it. The old version is automatically  
removed and replaced.

## Environment Variables Set by cc.bat

| Variable             | Value                          |
|----------------------|--------------------------------|
| `NPM_CONFIG_PREFIX`  | `<abs-path>\ai-env\tools\npm-global` |
