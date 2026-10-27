@echo off
title Check SNN campaign
echo.
echo    Checking whether the campaign is alive and progressing...
echo.
wsl.exe -e bash -c "cp '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/check_status.sh' /tmp/snn_chk_raw.sh && tr -d '\r' < /tmp/snn_chk_raw.sh > /tmp/snn_chk.sh && bash /tmp/snn_chk.sh"
echo.
pause
