@echo off
setlocal
cd /d "%~dp0"
if not exist config.json (
  echo ERROR: Configure config.json first using config.windows-example.json.
  echo This is not the TEST MEDIA mode.
  pause
  exit /b 1
)
if "%ZOOM_RTMS_CLIENT_ID%"=="" (
  echo ERROR: ZOOM_RTMS_CLIENT_ID is missing from this PowerShell session.
  pause
  exit /b 1
)
if "%ZOOM_RTMS_CLIENT_SECRET%"=="" (
  echo ERROR: ZOOM_RTMS_CLIENT_SECRET is missing from this PowerShell session.
  pause
  exit /b 1
)
if "%ZOOM_RTMS_EVENT_WSS%"=="" (
  echo ERROR: ZOOM_RTMS_EVENT_WSS is missing from this PowerShell session.
  pause
  exit /b 1
)
py -3 -c "import websocket" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Missing websocket-client. Install: py -3 -m pip install websocket-client
  pause
  exit /b 1
)
echo DocTutorials Zoom RTMS receiver - EXPERIMENTAL.
echo Authorized Zoom app, Developer Pack credits, consent and event WSS are required.
echo This build only correlates a UNIQUE concurrently scheduled class; otherwise fails closed.
echo Incoming Zoom Media has not been validated on this workstation.
py -3 controller.py --config config.json --rtms
pause
