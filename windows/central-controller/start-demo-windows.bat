@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo ERROR: Python 3 is required. Install from python.org.
 pause
 exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
 echo ERROR: FFmpeg is required and must be in Windows PATH.
 pause
 exit /b 1
)
py -3 -c "from PIL import Image" >nul 2>nul
if errorlevel 1 (
 echo ERROR: Install Pillow with: py -3 -m pip install Pillow
 pause
 exit /b 1
)
echo ================================================================
echo  DocTutorials - FOUR CHANNEL STANDALONE RECORDING DEMO
echo  SIMULATED teaching media - NOT connected to Zoom yet.
echo  Output: local Storage Center - real H.264/AAC MP4.
echo ================================================================
py -3 controller.py --demo
pause
