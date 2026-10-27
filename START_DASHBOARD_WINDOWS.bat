@echo off
setlocal
cd /d "%~dp0"
title SNN Benchmarking Dashboard - Safe Startup
set "LOG=%~dp0DASHBOARD_START_LOG.txt"
echo Starting dashboard on Windows. Details logged to "%LOG%".
echo START > "%LOG%"
where py >nul 2>nul
if not errorlevel 1 (
  set "PYCMD=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python not found. Install Python 3.10-3.12 and check "Add python.exe to PATH".
    echo Python missing >> "%LOG%"
    pause
    exit /b 1
  )
  set "PYCMD=python"
)
%PYCMD% -c "import sys; print(sys.version)" >> "%LOG%" 2>&1
if not exist ".dashboard_venv\Scripts\python.exe" (
  echo Creating isolated dashboard environment...
  %PYCMD% -m venv ".dashboard_venv" >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo Failed to create environment. See DASHBOARD_START_LOG.txt
    pause
    exit /b 1
  )
)
".dashboard_venv\Scripts\python.exe" -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo Installing Flask (internet required on the first launch)...
  ".dashboard_venv\Scripts\python.exe" -m pip install --disable-pip-version-check "Flask>=3.0,<4" >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo Flask installation failed. Check internet, proxy and DASHBOARD_START_LOG.txt
    echo You can still double-click OPEN_DASHBOARD_OFFLINE.html without Python.
    pause
    exit /b 1
  )
)
echo Checking local benchmark dataset...
".dashboard_venv\Scripts\python.exe" -c "from pathlib import Path; p=Path('results/benchmarks.db'); assert p.is_file(), 'Missing results/benchmarks.db'; import sqlite3; c=sqlite3.connect(str(p)); print('DB integrity', c.execute('pragma quick_check').fetchone()[0]); c.close()" >> "%LOG%" 2>&1
if errorlevel 1 (
 echo Results database missing/damaged; see log file.
 pause
 exit /b 1
)
echo Starting the dashboard; your browser opens automatically (the address is shown below).
".dashboard_venv\Scripts\python.exe" RUN_DASHBOARD.py
if errorlevel 1 echo Application exited unexpectedly; see DASHBOARD_START_LOG.txt.
echo Dashboard stopped. Press any key to close.
pause
