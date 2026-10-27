@echo off
title SNN campaign progress
wsl.exe -e bash -c "tr -d '\r' < '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/check_complete_campaign.sh' > /tmp/snn_check_complete.sh && bash /tmp/snn_check_complete.sh"
echo.
pause
