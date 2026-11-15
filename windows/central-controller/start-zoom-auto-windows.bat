@echo off
setlocal
cd /d "%~dp0"
if not exist config.json (
  echo ERROR: Windows Storage Center config.json missing.
  exit /b 1
)
if "%ZOOM_EVENTS_CLIENT_ID%"=="" (
  echo ERROR: ZOOM_EVENTS_CLIENT_ID missing. Configure Zoom meeting EVENT subscription, not RTMS.
  exit /b 1
)
if "%ZOOM_EVENTS_CLIENT_SECRET%"=="" (
  echo ERROR: ZOOM_EVENTS_CLIENT_SECRET missing.
  exit /b 1
)
if "%ZOOM_EVENTS_WSS%"=="" (
  echo ERROR: ZOOM_EVENTS_WSS missing.
  exit /b 1
)
if /i not "%DOCTUTORIALS_AUTO_NOTICE_CONFIRMED%"=="YES" (
  echo ERROR: Institutional recording notice/consent policy has not been approved.
  echo Set DOCTUTORIALS_AUTO_NOTICE_CONFIRMED=YES after confirming permission and notices.
  exit /b 1
)
py -3 -c "import websocket, PIL, soundcard, numpy" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Missing Python dependency. Install: py -3 -m pip install websocket-client pillow soundcard numpy
  exit /b 1
)
echo DocTutorials AUTO Zoom meeting event listener + Windows Zoom Workplace capture.
echo No RTMS, no Zoom Cloud Recording and no manual per-class capture buttons.
echo A visible Zoom desktop meeting window and authorized join/recording remain required.
echo WARNING: This is a one-meeting experimental build. Four isolated meetings are NOT ready.
py -3 controller.py --config config.json --desktop --auto-desktop