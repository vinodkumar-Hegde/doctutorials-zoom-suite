@echo off
setlocal
cd /d "%~dp0"
py -3 zoom_rtms_preflight.py %*
pause
