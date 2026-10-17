@echo off
title AuditAI - AI Expense Audit & Fraud Detection Platform
echo ========================================================
echo   AuditAI - Soft Computing Expense Fraud Detection
echo ========================================================
echo.

cd /d "%~dp0"

echo Checking if server is already running...
python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5001/health', timeout=1).getcode() == 200 else 1)" 2>nul
if %ERRORLEVEL% equ 0 (
    echo Server is ALREADY running on http://localhost:5001!
    echo Opening dashboard in your default browser...
    start http://localhost:5001/dashboard
    goto end
)

echo Starting server and launching browser...
start "" http://localhost:5001/dashboard
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5001

:end
pause
