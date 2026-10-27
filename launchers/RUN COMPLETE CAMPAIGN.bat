@echo off
title SNN complete campaign - instrumented training
echo.
echo    COMPLETE CAMPAIGN
echo.
echo    Every experiment, every backend, nothing skipped.
echo    Training now measures processor utilisation, the energy
echo    proxy and peak memory - the gap the thesis had to declare.
echo.
echo    The thesis database is NOT touched. This writes its own.
echo    Safe to re-run: phases already finished are skipped.
echo    Closing this window does NOT stop it.
echo.
wsl.exe -e bash -c "tr -d '\r' < '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/run_complete_campaign.sh' > /tmp/snn_launch_complete.sh && bash /tmp/snn_launch_complete.sh"
echo.
pause
