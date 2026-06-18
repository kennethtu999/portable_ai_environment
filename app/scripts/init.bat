@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ============================================================
:: VERSION CONFIG
:: ============================================================
set WINPYTHON_URL=https://github.com/winpython/winpython/releases/download/17.4.20260511final/WinPython64-3.13.13.0dot.zip
set NODE_URL=https://nodejs.org/dist/v24.16.0/node-v24.16.0-win-x64.zip
set MINGIT_URL=https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/MinGit-2.49.0-64-bit.zip
set RG_URL=https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-x86_64-pc-windows-msvc.zip
set JQ_URL=https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-windows-amd64.exe
set JQ_VERSION=1.7.1
:: ============================================================

:: Step 1: Python (WinPython)
set WINPYTHON_ZIP=
for %%f in (WinPython*.zip WPy*.zip) do (
  if exist "%%f" set WINPYTHON_ZIP=%%f
)
if not exist "python\" (
  if not defined WINPYTHON_ZIP (
    echo [setup] WinPython not found. Downloading...
    curl -L --progress-bar -o WinPython.tmp.zip "!WINPYTHON_URL!"
    if errorlevel 1 (echo [error] Failed to download WinPython. & pause & exit /b 1)
    set WINPYTHON_ZIP=WinPython.tmp.zip
  )
  echo [setup] Extracting WinPython from !WINPYTHON_ZIP!...
  mkdir python
  tar -xf "!WINPYTHON_ZIP!" -C python
  if errorlevel 1 (echo [error] Failed to extract WinPython. & pause & exit /b 1)
  if "!WINPYTHON_ZIP!"=="WinPython.tmp.zip" del /f /q WinPython.tmp.zip
)

:: Step 2: Node.js
set NODE_ZIP=
for %%f in (node-v*.zip) do (
  if exist "%%f" set NODE_ZIP=%%f
)
if not exist "tools\node\node.exe" (
  if not defined NODE_ZIP (
    echo [setup] Node.js not found. Downloading...
    curl -L --progress-bar -o node.tmp.zip "!NODE_URL!"
    if errorlevel 1 (echo [error] Failed to download Node.js. & pause & exit /b 1)
    set NODE_ZIP=node.tmp.zip
  )
  echo [setup] Extracting Node.js from !NODE_ZIP!...
  if exist tools\node rd /s /q tools\node
  mkdir tools\node
  tar -xf "!NODE_ZIP!" -C tools\node --strip-components=1
  if errorlevel 1 (echo [error] Failed to extract Node.js. & pause & exit /b 1)
  if "!NODE_ZIP!"=="node.tmp.zip" del /f /q node.tmp.zip
)

:: Step 2.5: npm global prefix
mkdir tools\npm-global 2>nul

:: Step 3: MinGit
set MINGIT_ZIP=
for %%f in (MinGit-*.zip) do (
  if exist "%%f" set MINGIT_ZIP=%%f
)
if not exist "tools\git\cmd\git.exe" (
  if not defined MINGIT_ZIP (
    echo [setup] MinGit not found. Downloading...
    curl -L --progress-bar -o MinGit.tmp.zip "!MINGIT_URL!"
    if errorlevel 1 (echo [error] Failed to download MinGit. & pause & exit /b 1)
    set MINGIT_ZIP=MinGit.tmp.zip
  )
  echo [setup] Extracting MinGit from !MINGIT_ZIP!...
  if exist tools\git rd /s /q tools\git
  mkdir tools\git
  tar -xf "!MINGIT_ZIP!" -C tools\git
  if errorlevel 1 (echo [error] Failed to extract MinGit. & pause & exit /b 1)
  if "!MINGIT_ZIP!"=="MinGit.tmp.zip" del /f /q MinGit.tmp.zip
)

:: Step 4: ripgrep
set RG_ZIP=
for %%f in (ripgrep-*.zip) do (
  if exist "%%f" set RG_ZIP=%%f
)
if not exist "tools\rg\rg.exe" (
  if not defined RG_ZIP (
    echo [setup] ripgrep not found. Downloading...
    curl -L --progress-bar -o ripgrep.tmp.zip "!RG_URL!"
    if errorlevel 1 (echo [error] Failed to download ripgrep. & pause & exit /b 1)
    set RG_ZIP=ripgrep.tmp.zip
  )
  echo [setup] Extracting ripgrep from !RG_ZIP!...
  if exist tools\rg rd /s /q tools\rg
  mkdir tools\rg
  tar -xf "!RG_ZIP!" -C tools\rg --strip-components=1
  if errorlevel 1 (echo [error] Failed to extract ripgrep. & pause & exit /b 1)
  if "!RG_ZIP!"=="ripgrep.tmp.zip" del /f /q ripgrep.tmp.zip
)

:: Step 5: jq
if not exist "tools\jq\jq.exe" (
  echo [setup] Downloading jq %JQ_VERSION%...
  if exist tools\jq rd /s /q tools\jq
  mkdir tools\jq
  curl -L --progress-bar -o "tools\jq\jq.exe" "!JQ_URL!"
  if errorlevel 1 (echo [error] Failed to download jq. & pause & exit /b 1)
)

:: Step 6: venv + packages + MarkItDown health check (first run only)
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

:: Step 7: API key setup
echo [env] Checking API key...
.venv\Scripts\python.exe scripts\setup_env.py
if errorlevel 1 (pause & exit /b 1)

:: Step 8: Claude API health check
echo [health] Running Claude health check...
.venv\Scripts\python.exe scripts\health_claude.py
if errorlevel 1 (pause & exit /b 1)

:: Step 9: Claude CLI install (local, no -g)
call :setup_node_path

if not exist "tools\npm-global\node_modules\.bin\claude.cmd" (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo [error] npm not found. Cannot install Claude CLI.
    pause & exit /b 1
  )
  echo [setup] Installing Claude CLI...
  cd tools\npm-global
  npm install @anthropic-ai/claude-code
  cd ..\..
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
