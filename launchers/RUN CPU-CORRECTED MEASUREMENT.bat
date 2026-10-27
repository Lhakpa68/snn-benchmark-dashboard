@echo off
title SNN CPU-corrected measurement
echo.
echo    CPU-corrected re-measurement: inference + scalability, all 11 backends
echo    About 10 minutes. Please leave this window open and the laptop plugged in.
echo    Avoid using the laptop heavily while it runs.
echo.
wsl.exe -e bash -c "tr -d '\r' < '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/run_cpu_corrected.sh' > /tmp/snn_cpufix.sh && bash /tmp/snn_cpufix.sh"
echo.
pause
