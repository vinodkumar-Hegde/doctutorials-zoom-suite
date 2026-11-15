# DocTutorials Central Controller — Windows only

**This version runs the Admin session schedule, four recorder channels and local Storage Center on ONE Windows computer. No Mac session bridge, Mac IP, certificate fingerprint, or pairing password is required.**

The Admin schedule is a local SQLite database saved beside the recorder's data, so it survives restarts. You can create a class, enter course/subject/topic/faculty, schedule a time, optionally reserve a channel, and cancel a scheduled class. Channel conflicts are rejected. The scheduling UI does NOT create Zoom meetings and it does NOT detect whether a meeting is currently live.

## Update the existing Windows installation

Use **Windows PowerShell** on the recording computer (the one already running Python, FFmpeg and Visual Studio):

```powershell
cd "$HOME\doctutorials-zoom-suite"
git pull
cd .\windows\central-controller
py -3 -m unittest discover -s tests -v
.\start-demo-windows.bat
```

First press Ctrl+C to stop the old Central Controller process if it is already running. Open **http://127.0.0.1:8780** on that same Windows PC, sign in with the password you create in the controller window, then choose **Assign Class**. No additional installation or downloads needed for the scheduler. It does not depend on port 8443 or 8444.

If you want to use the ZIP rather than Git, the updated GitHub source ZIP is at `windows/central-controller/DocTutorials-Central-Controller-Windows.zip` and extracts to a `DocTutorials-Central-Controller` directory. It is not needed for an existing Git checkout.

## Recorder status — read this before testing with a class

- **Demo mode** (`start-demo-windows.bat`) uses FFmpeg test-pattern media. Its channel buttons say **Run TEST MEDIA**. Those MP4s are real files but NOT Zoom class recordings.
- **Configured-input mode** (`start-recorder-windows.bat`) can record real Windows sources set in local, private `config.json`, subject to permissions, independent screen/audio sources and verification. It has NOT been proven to record a complete Zoom class or four parallel Zoom meetings.
- **Zoom raw-media connector and automatic Zoom joining are not included**. Installing Visual Studio does not supply either the Zoom SDK or working media integration.
- **Faculty iPad and laptop access to the Windows schedule is not yet wired**. This locally available Admin scheduler is the next working foundation, not an end-to-end teaching solution.
- The controller is currently loopback-only (`127.0.0.1:8780`). Do not port-forward it to faculty devices, the LAN, or the internet.

The system does not rely on OBS or Zoom Cloud Recording, and its storage library retains verified local MP4s when NAS archive attempts fail.

Only authorized classes should be recorded, with required participant notice and Zoom permissions. Keep credentials, actual meeting invitations, private configuration and recordings out of GitHub.
