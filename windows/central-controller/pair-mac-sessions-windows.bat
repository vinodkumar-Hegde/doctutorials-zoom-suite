@echo off
setlocal
cd /d "%~dp0"
py -3 pair_mac_sessions.py
pause
