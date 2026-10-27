@echo off
title Inspect python environments
echo.
echo    Stopping any running campaign and taking an inventory of every
echo    Python environment on this machine. Nothing will be launched.
echo.
wsl.exe -e bash -c "cp '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/prepare_environment.sh' /tmp/snn_prep_raw.sh && tr -d '\r' < /tmp/snn_prep_raw.sh > /tmp/snn_prep.sh && bash /tmp/snn_prep.sh"
echo.
echo    Done.
pause
