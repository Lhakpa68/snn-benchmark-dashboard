@echo off
REM Legacy WSL-only starter. For ordinary Windows use ../START_DASHBOARD_WINDOWS.bat.
REM Starts the dashboard inside WSL and opens it in your browser.
REM Double-click this file. The URL below assumes the shipped default port
REM in dashboard_config.py (5000); if you change PORT there, open that
REM address instead once the server prints it.
setlocal
cd /d "%~dp0"

echo Starting the dashboard inside WSL...
echo.
echo   It will be at  http://127.0.0.1:5000
echo   Leave this window open. Close it to stop the server.
echo.

start "" http://127.0.0.1:5000

wsl -e bash -lc "cd \"$(wslpath '%CD%')\" && chmod +x START_DASHBOARD.sh && ./START_DASHBOARD.sh"

pause
