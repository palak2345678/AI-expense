@echo off
title Push AI-Expense to GitHub
cd /d "%~dp0"

set "GIT_EXE=git"
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    if exist "C:\Users\palak\.gemini\antigravity\bin\mingit\cmd\git.exe" (
        set "GIT_EXE=C:\Users\palak\.gemini\antigravity\bin\mingit\cmd\git.exe"
    )
)

echo ========================================================
echo   Pushing All CSS, JS, HTML, and Models to GitHub
echo ========================================================
echo.
echo Pushing branch master to GitHub main...
"%GIT_EXE%" push -u origin master:main --force
echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo   SUCCESS! All files, CSS, and JS pushed to GitHub!
    echo   Render will automatically detect this commit and redeploy.
    echo ========================================================
) else (
    echo ========================================================
    echo   Push encountered an authorization prompt or error.
    echo   If a browser window or login prompt opened, please sign in.
    echo ========================================================
)
echo.
pause
