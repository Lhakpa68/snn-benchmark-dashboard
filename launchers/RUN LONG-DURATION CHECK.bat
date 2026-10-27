@echo off
title SNN long-duration check (1 s window)
echo.
echo    Journal revision: scalability sweep with a 1 s simulated window.
echo    This can take one to three hours. Leave the window open and the laptop plugged in.
echo.
wsl.exe -e bash -c "tr -d '\r' < '/mnt/c/Users/Tsher/OneDrive/Desktop/LT Final Theis Files/SNN_Benchmark_Dashboard_V6_Final/SNN_Benchmark_Dashboard/launchers/run_long_duration.sh' > /tmp/snn_long.sh && bash /tmp/snn_long.sh"
echo.
pause
