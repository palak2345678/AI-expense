@echo off
title AuditAI - Streamlit Application
echo ========================================================
echo   AuditAI - Soft Computing Expense Fraud Detection
echo               (Streamlit Cloud Edition)
echo ========================================================
echo.
cd /d "%~dp0"
echo Launching Streamlit App in browser...
python -m streamlit run streamlit_app.py
pause
