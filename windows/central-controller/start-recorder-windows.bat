@echo off
setlocal
cd /d "%~dp0"
if not exist "config.json" (
 echo No production config found.
 echo Copy config.windows-example.json to config.json and configure verified input sources.
 echo IMPORTANT: Do not mark a channel configured until it receives real media.
 pause
 exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (echo FFmpeg missing from PATH. & pause & exit /b 1)
py -3 -c "from PIL import Image" >nul 2>nul
if errorlevel 1 (echo Pillow missing. Run: py -3 -m pip install Pillow soundcard numpy & pause & exit /b 1)
py -3 controller.py --config config.json
pause
