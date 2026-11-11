@echo off
setlocal
title ForestWatch AI - Unified Sentinel Launcher
cd /d "%~dp0"

echo ========================================================================
echo       ForestWatch AI - Starting Multi-Subsystem Platform
echo ========================================================================

if exist ".venv\Scripts\python.exe" (
    echo [*] Using virtual environment python: .venv\Scripts\python.exe
    ".venv\Scripts\python.exe" runproj.py %*
) else (
    echo [*] Using system python
    python runproj.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Process exited with code %ERRORLEVEL%
    pause
)

