@echo off
title FRIDAY - Stopping...
color 0C

echo.
echo  Stopping all FRIDAY processes...
echo.

taskkill /FI "WINDOWTITLE eq FRIDAY - Hermes Gateway" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FRIDAY - UI + Bridge"    /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FRIDAY - Voice Pipeline" /F >nul 2>&1

:: Also kill by process name as fallback
taskkill /IM "hermes.exe" /F >nul 2>&1

echo  [OK] All FRIDAY processes stopped.
echo.
pause
