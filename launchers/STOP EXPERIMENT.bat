@echo off
title STOP SNN experiment
echo.
echo    Stopping any running SNN benchmark campaign...
echo.
wsl.exe -e bash -c "pkill -f 'run.py bench'; pkill -f 'run.py validate'; pkill -f snn_launch; pkill -f snn_run.sh; sleep 1; if pgrep -f 'run.py' > /dev/null; then echo 'STILL RUNNING:'; pgrep -af 'run.py'; else echo 'Stopped. No benchmark process is running.'; fi"
echo.
pause
