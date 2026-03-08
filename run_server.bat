@echo off
title MaxHub Local Server
echo ========================================
echo   MaxHub Local Server - Dev Mode
echo   http://127.0.0.1:8000
echo   Press Ctrl+C to stop
echo ========================================
echo.
cd /d "%~dp0"
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --workers 1 --reload --log-level info
pause
