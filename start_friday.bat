@echo off
title FRIDAY - Starting...
color 0B

echo.
echo  ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗
echo  ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝
echo  █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝ 
echo  ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝  
echo  ██║     ██║  ██║██║██████╔╝██║  ██║   ██║   
echo  ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝  
echo.
echo  Fully Responsive Intelligence Digital Assistant Yeah
echo  =====================================================
echo.

:: ── Check hermes is available ──────────────────────────────
where hermes >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] hermes not found in PATH. Install Hermes Agent first.
    pause
    exit /b 1
)

:: ── Check node is available ────────────────────────────────
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] node not found. Install Node.js first.
    pause
    exit /b 1
)

:: ── Check python is available ──────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] python not found. Install Python first.
    pause
    exit /b 1
)

echo  [1/3] Starting Hermes Gateway...
start "FRIDAY - Hermes Gateway" cmd /k "title FRIDAY - Hermes Gateway && color 0A && hermes gateway"

timeout /t 2 /nobreak >nul

echo  [2/3] Starting UI + Bridge Server...
start "FRIDAY - UI + Bridge" cmd /k "title FRIDAY - UI + Bridge && color 0B && cd /d %~dp0 && npm run dev"

timeout /t 2 /nobreak >nul

echo  [3/3] Starting Voice Pipeline...
:: Check if venv exists, use it; otherwise use system python
if exist "%~dp0voice\venv\Scripts\python.exe" (
    start "FRIDAY - Voice" cmd /k "title FRIDAY - Voice Pipeline && color 0E && cd /d %~dp0voice && venv\Scripts\python.exe friday_voice.py"
) else (
    start "FRIDAY - Voice" cmd /k "title FRIDAY - Voice Pipeline && color 0E && cd /d %~dp0voice && python friday_voice.py"
)

timeout /t 3 /nobreak >nul

echo.
echo  =====================================================
echo  [OK] All systems launching...
echo  [OK] UI will be ready at http://localhost:5173
echo  [OK] Close this window or press any key to exit
echo  =====================================================
echo.
echo  To stop FRIDAY, close all three terminal windows.
echo.
pause
