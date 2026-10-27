@echo off
title SNN instrument smoke test
echo.
echo    Proving the new training instrumentation on a tiny budget.
echo    About 10-20 minutes. Nothing existing is touched.
echo.
wsl.exe -e bash -c "tr -d '\r' < '/mnt/d/MIT College/Last Edition/SNN Simulator Benchmark - Final/launchers/smoke_training_instruments.sh' > /tmp/snn_smoke.sh && bash /tmp/snn_smoke.sh"
echo.
pause
