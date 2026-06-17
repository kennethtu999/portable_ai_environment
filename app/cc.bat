@echo off
setlocal
cd /d "%~dp0"

:: Project folder is the parent of ai-env
for %%i in ("%~dp0..") do set PROJ=%%~fi

where wt.exe >nul 2>nul
if %errorlevel%==0 (
  start "" wt.exe -d "%PROJ%" powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\shell.ps1"
) else (
  powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0scripts\shell.ps1"
)
