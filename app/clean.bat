@echo off
setlocal
set CONFIG=%USERPROFILE%\.portable_ai_environment\claude.env

echo [clean] Removing API configuration...
echo.

if not exist "%CONFIG%" (
  echo [info] No configuration found at:
  echo        %CONFIG%
  echo.
  echo Nothing to remove.
) else (
  del /f /q "%CONFIG%"
  if errorlevel 1 (
    echo [error] Failed to remove %CONFIG%
  ) else (
    echo [done] Removed: %CONFIG%
    echo.
    echo Run ai-env\init.bat to set up a new configuration.
  )
)

echo.
pause
