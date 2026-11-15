@echo off
setlocal
cd /d "%~dp0"
echo DocTutorials Zoom event CONNECTION DIAGNOSTIC - does not record or join a meeting.
echo Stop the existing Zoom auto controller first so its event connection is not disturbed.
py -3 zoom_events_diagnostic.py
