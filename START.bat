@echo off
title IGRIS — Forge Yourself
color 0A
cls

echo.
echo    ██╗ ██████╗ ██████╗ ██╗███████╗
echo    ██║██╔════╝ ██╔══██╗██║██╔════╝
echo    ██║██║  ███╗██████╔╝██║███████╗
echo    ██║██║   ██║██╔══██╗██║╚════██║
echo    ██║╚██████╔╝██║  ██║██║███████║
echo    ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝
echo.
echo    Forge Yourself Daily
echo    ─────────────────────────────────

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo    [ERROR] Node.js not found - download from nodejs.org
    pause & exit /b 1
)

cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "data\brain_data.json" echo {} > data\brain_data.json

echo    Starting on port 3737... browser opens automatically.
echo    Keep this window open.
echo.

node server.js
pause >nul
