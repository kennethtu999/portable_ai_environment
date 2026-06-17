@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ── VERSION CONFIG ────────────────────────────────────────────────────────────
set WINPYTHON_FILE=WinPython64-3.13.13.0dot.zip
set WINPYTHON_URL=https://github.com/winpython/winpython/releases/download/17.4.20260511final/WinPython64-3.13.13.0dot.zip

set NODE_FILE=node-v24.16.0-win-x64.zip
set NODE_URL=https://nodejs.org/dist/v24.16.0/node-v24.16.0-win-x64.zip

set MINGIT_FILE=MinGit-2.49.0-64-bit.zip
set MINGIT_URL=https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/MinGit-2.49.0-64-bit.zip

set RG_FILE=ripgrep-14.1.1-x86_64-pc-windows-msvc.zip
set RG_URL=https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-pc-windows-msvc.zip

set JQ_VERSION=1.7.1
set JQ_URL=https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
:: ─────────────────────────────────────────────────────────────────────────────

:: ── Step 1: Python (WinPython) ────────────────────────────────────────────────
if not exist "python\" (
  if not exist "!WINPYTHON_FILE!" (
    echo [setup] WinPython not found. Downloading !WINPYTHON_FILE!...
    curl -L --progress-bar -o "!WINPYTHON_FILE!" "!WINPYTHON_URL!"
    if errorlevel 1 (echo [error] Failed to download WinPython. & pause & exit /b 1)
  )
  echo [setup] Extracting WinPython...
  mkdir python
  tar -xf "!WINPYTHON_FILE!" -C python
  if errorlevel 1 (echo [error] Failed to extract WinPython. & pause & exit /b 1)
)

:: ── Step 2: Node.js → tools\node ─────────────────────────────────────────────
:: Marker tracks installed version; bumping NODE_FILE triggers re-download.
:: Node ZIP has a wrapper dir → strip-components=1 puts node.exe in tools\node\
set NODE_MARKER=tools\node\.installed-%NODE_FILE%
if not exist "!NODE_MARKER!" (
  if not exist "!NODE_FILE!" (
    echo [setup] Node.js not found. Downloading !NODE_FILE!...
    curl -L --progress-bar -o "!NODE_FILE!" "!NODE_URL!"
    if errorlevel 1 (echo [error] Failed to download Node.js. & pause & exit /b 1)
  )
  echo [setup] Extracting Node.js...
  if exist tools\node rd /s /q tools\node
  mkdir tools\node
  tar -xf "!NODE_FILE!" -C tools\node --strip-components=1
  if errorlevel 1 (echo [error] Failed to extract Node.js. & pause & exit /b 1)
  echo. > "!NODE_MARKER!"
)

:: ── Step 2.5: npm global prefix → tools\npm-global ──────────────────────────
:: Global npm installs (e.g. claude CLI) land inside ai-env, not the system.
mkdir tools\npm-global 2>nul

:: ── Step 3: MinGit → tools\git ───────────────────────────────────────────────
:: MinGit ZIP is flat (cmd\git.exe at root) → no strip needed.
set MINGIT_MARKER=tools\git\.installed-%MINGIT_FILE%
if not exist "!MINGIT_MARKER!" (
  if not exist "!MINGIT_FILE!" (
    echo [setup] MinGit not found. Downloading !MINGIT_FILE!...
    curl -L --progress-bar -o "!MINGIT_FILE!" "!MINGIT_URL!"
    if errorlevel 1 (echo [error] Failed to download MinGit. & pause & exit /b 1)
  )
  echo [setup] Extracting MinGit...
  if exist tools\git rd /s /q tools\git
  mkdir tools\git
  tar -xf "!MINGIT_FILE!" -C tools\git
  if errorlevel 1 (echo [error] Failed to extract MinGit. & pause & exit /b 1)
  echo. > "!MINGIT_MARKER!"
)

:: ── Step 4: ripgrep → tools\rg ───────────────────────────────────────────────
:: ripgrep ZIP has a wrapper dir → strip-components=1 puts rg.exe in tools\rg\
set RG_MARKER=tools\rg\.installed-%RG_FILE%
if not exist "!RG_MARKER!" (
  if not exist "!RG_FILE!" (
    echo [setup] ripgrep not found. Downloading !RG_FILE!...
    curl -L --progress-bar -o "!RG_FILE!" "!RG_URL!"
    if errorlevel 1 (echo [error] Failed to download ripgrep. & pause & exit /b 1)
  )
  echo [setup] Extracting ripgrep...
  if exist tools\rg rd /s /q tools\rg
  mkdir tools\rg
  tar -xf "!RG_FILE!" -C tools\rg --strip-components=1
  if errorlevel 1 (echo [error] Failed to extract ripgrep. & pause & exit /b 1)
  echo. > "!RG_MARKER!"
)

:: ── Step 5: jq → tools\jq ────────────────────────────────────────────────────
:: Single exe download; marker tracks version.
set JQ_MARKER=tools\jq\.installed-jq-%JQ_VERSION%
if not exist "!JQ_MARKER!" (
  echo [setup] Downloading jq %JQ_VERSION%...
  if exist tools\jq rd /s /q tools\jq
  mkdir tools\jq
  curl -L --progress-bar -o "tools\jq\jq.exe" "!JQ_URL!"
  if errorlevel 1 (echo [error] Failed to download jq. & pause & exit /b 1)
  echo. > "!JQ_MARKER!"
)

:: ── Step 6: venv + packages + MarkItDown health check (first run only) ────────
if not exist ".venv\Scripts\python.exe" (
  call :detect_python
  if "!PYTHON_CMD!"=="" (
    echo [error] Python not found.
    echo [info]  Option 1: Place WinPython64-*.zip in this folder.
    echo [info]  Option 2: Install Python 3 from https://www.python.org/downloads/
    pause & exit /b 1
  )
  echo [setup] Using Python: !PYTHON_CMD!

  echo [setup] Creating virtual environment...
  "!PYTHON_CMD!" -m venv .venv
  if errorlevel 1 (echo [error] venv creation failed. & pause & exit /b 1)

  echo [setup] Installing packages...
  .venv\Scripts\python.exe -m pip install --upgrade pip -q
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (echo [error] Package installation failed. & pause & exit /b 1)

  echo [health] Running MarkItDown health check...
  .venv\Scripts\python.exe scripts\health_markitdown.py
  if errorlevel 1 (echo [error] MarkItDown health check failed. & pause & exit /b 1)

  del /f /q "test_docs\sample.docx" "test_docs\sample.xlsx" "test_docs\sample.pdf" 2>nul
  echo [health] Sample docs removed.
)

:: ── Step 7: API key setup (skips if already configured) ──────────────────────
echo [env] Checking API key...
.venv\Scripts\python.exe scripts\setup_env.py
if errorlevel 1 (pause & exit /b 1)

:: ── Step 8: Claude API health check ──────────────────────────────────────────
echo [health] Running Claude health check...
.venv\Scripts\python.exe scripts\health_claude.py
if errorlevel 1 (pause & exit /b 1)

:: ── Step 9: Claude CLI install ────────────────────────────────────────────────
call :setup_node_path

where claude >nul 2>&1
if errorlevel 1 (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo [error] npm not found. Cannot install Claude CLI.
    pause & exit /b 1
  )
  echo [setup] Installing Claude CLI...
  npm install -g @anthropic-ai/claude-code
  if errorlevel 1 (echo [error] Claude CLI install failed. & pause & exit /b 1)
)

echo.
echo [done] Environment ready. Run cc.bat to start.
pause
exit /b 0

:setup_node_path
for /f "delims=" %%f in ('where /r tools\node node.exe 2^>nul') do (
  if "!NODE_BIN_DIR!"=="" (
    set NODE_BIN_DIR=%%~dpf
    set PATH=!NODE_BIN_DIR!;!PATH!
  )
)
set NPM_CONFIG_PREFIX=%CD%\tools\npm-global
set PATH=%CD%\tools\npm-global;%PATH%
exit /b 0

:detect_python
set PYTHON_CMD=
for /f "delims=" %%f in ('where /r python python.exe 2^>nul') do (
  if "!PYTHON_CMD!"=="" set PYTHON_CMD=%%f
)
if defined PYTHON_CMD exit /b 0
where py >nul 2>&1
if not errorlevel 1 (
  py -3 --version >nul 2>&1
  if not errorlevel 1 set PYTHON_CMD=py -3
)
if defined PYTHON_CMD exit /b 0
where python3 >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python3
if defined PYTHON_CMD exit /b 0
where python >nul 2>&1
if not errorlevel 1 set PYTHON_CMD=python
exit /b 0
