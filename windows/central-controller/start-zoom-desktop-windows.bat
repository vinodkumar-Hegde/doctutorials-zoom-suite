@echo off
setlocal
cd /d "%~dp0"
if not exist config.json (
 echo ERROR: Local config.json is missing. Run the previously provided Windows setup step.
 pause
 exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (echo ERROR: FFmpeg unavailable & pause & exit /b 1)
py -3 -c "from PIL import Image; import soundcard; import numpy" >nul 2>nul
if errorlevel 1 (
 echo Windows audio capture requires soundcard and numpy: py -3 -m pip install soundcard numpy
 echo Pillow must also be available.
 pause
 exit /b 1
)
echo DocTutorials Zoom Workplace desktop capture — ONE meeting, operator assisted.
echo No RTMS, OBS or Zoom Cloud Recording used.
echo The private Zoom join registry must exist locally; joining does not start a recording.
py -3 controller.py --config config.json --desktop
pause
