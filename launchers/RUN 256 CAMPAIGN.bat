@echo off
title SNN campaign - hidden 256
echo.
echo    CCR campaign at hidden width 256
echo    60,000 train / 10,000 test / 10 epochs
echo    Every training-capable backend. Nothing skipped.
echo.
echo    Safe to re-run: phases already finished are skipped.
echo    Closing this window does NOT stop it.
echo.
wsl.exe -e bash -c "tr -d '\r' < '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/run_256_campaign.sh' > /tmp/snn_launch256.sh && bash /tmp/snn_launch256.sh"
echo.
pause
