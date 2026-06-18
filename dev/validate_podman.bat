@echo off
:: 用途：從 ZIP 模擬使用者「下載 → 解壓 → 執行」流程，在乾淨 Podman 容器中驗證
:: 使用方式：
::   scripts\validate_podman.bat
::   set ANTHROPIC_API_KEY=sk-ant-xxx && scripts\validate_podman.bat
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

where podman >nul 2>&1
if errorlevel 1 (
  echo [error] Podman not found. Install: https://podman.io/getting-started/installation
  pause
  exit /b 1
)

set IMAGE=python:3.11-slim
set ZIP_FILE=%TEMP%\portable_claude_env_validate.zip

:: Create ZIP (simulate GitHub release ZIP)
echo [validate] Creating ZIP from current directory...
python -c "
import zipfile, pathlib
exclude = {'.venv', 'output', '__pycache__'}
with zipfile.ZipFile(r'%ZIP_FILE%', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in pathlib.Path('.').rglob('*'):
        parts = set(f.parts)
        if f.is_file() and not parts & exclude:
            z.write(str(f))
print('[validate] ZIP created: %ZIP_FILE%')
"
if errorlevel 1 (
  echo [error] Failed to create ZIP.
  pause
  exit /b 1
)

echo [validate] Pulling image: %IMAGE%
podman pull %IMAGE% --quiet

set CLAUDE_BLOCK=
if defined ANTHROPIC_API_KEY (
  set CLAUDE_BLOCK=echo [container] Step d: Claude health check... && mkdir -p $HOME/.portable_ai_environment && printf 'ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY%\n' > $HOME/.portable_ai_environment/.env && .venv/bin/python scripts/health_claude.py
)

echo [validate] Running bootstrap from ZIP in clean container...
podman run --rm ^
  -v "%ZIP_FILE%:/tmp/test.zip:ro" ^
  %IMAGE% ^
  bash -c "set -e && apt-get update -qq && apt-get install -y unzip -qq 2>/dev/null && mkdir -p /tmp/app && cd /tmp/app && echo '[container] Extracting ZIP...' && unzip -q /tmp/test.zip && echo '[container] Step a: Creating venv...' && python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip -q && .venv/bin/python -m pip install -r requirements.txt -q && echo '[container] Step b: MarkItDown health check...' && .venv/bin/python scripts/health_markitdown.py && rm -f test_docs/sample.docx test_docs/sample.xlsx test_docs/sample.pdf && echo '[container] All checks passed.'"

if errorlevel 1 (
  echo [error] Validation failed.
  pause
  exit /b 1
)

echo [validate] Done. Bootstrap validated from ZIP in clean Podman environment.
pause
