# DocTutorials Central Controller — Windows install / operator notes

This is an **experimental four-channel local recording and MP4/NAS storage engine**, not a Zoom Meeting SDK connector. Its demo uses **synthetic test media**, not a real Zoom class. It listens on `127.0.0.1:8780` on the Windows PC. Do not expose the port outside that machine.

## Requirements

Windows 10/11; Python 3 with `py` launcher; FFmpeg + ffprobe in PATH; Python Pillow package. These commands require PowerShell (not Command Prompt).

If Python or FFmpeg are missing, Windows Package Manager can install them:

```powershell
winget install --id Python.Python.3.13 --exact
winget install --id Gyan.FFmpeg --exact
```

Close and reopen PowerShell after installation. If your workplace has managed software policies, have IT install these from approved sources instead.

Check prerequisites:

```powershell
py -3 --version
ffmpeg -version
ffprobe -version
py -3 -m pip install Pillow
```

## Download from the DocTutorials GitHub repository (no Git client needed)

```powershell
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:USERPROFILE 'DocTutorials-Central'
New-Item -ItemType Directory -Force -Path $base | Out-Null
$url = 'https://raw.githubusercontent.com/vinodkumar-Hegde/doctutorials-zoom-suite/main/windows/central-controller/DocTutorials-Central-Controller-Windows.zip'
$zip = Join-Path $base 'DocTutorials-Central-Controller-Windows.zip'
Invoke-WebRequest -Uri $url -OutFile $zip
Expand-Archive -LiteralPath $zip -DestinationPath $base -Force
Set-Location (Join-Path $base 'DocTutorials-Central-Controller')
py -3 -m pip install Pillow
.\start-demo-windows.bat
```

Open `http://127.0.0.1:8780` **on the same Windows machine**. Create a private 12+ character password in the console, log in, and test each of the four **TEST MEDIA** channels. After each test finishes, use Storage Center Play/Download to verify the actual MP4.

## Git clone alternative (source files directly)

```powershell
git clone https://github.com/vinodkumar-Hegde/doctutorials-zoom-suite.git
Set-Location .\doctutorials-zoom-suite\windows\central-controller
py -3 -m pip install Pillow
.\start-demo-windows.bat
```

## Tests

```powershell
py -3 -m unittest discover -s tests -v
```

## Connect your existing Mac Admin assigned classes (new)

The Windows dashboard now has **Assigned Sessions** ABOVE the four channels. Those
cards come from the existing Mac DocTutorials Admin SQLite database; they are NOT
Zoom's 'currently in meeting' state and do not start/stop Zoom automatically.

The existing Mac admin server on `127.0.0.1:8443` stays unchanged. A separate
read-only LAN HTTPS bridge runs on Mac port `8444`. It transmits ONLY: sessionId,
facultyId, course, subject, topic, startsAt, endsAt. No Zoom meeting number,
passcode, faculty login, SDK credentials, JWT, join link or recording is sent.

**On Mac**, download this repository's `windows/central-controller/mac_session_bridge.py`
to your Mac (or pull the repo on Mac), then run it with `python3` while keeping
your existing HTTPS Admin dashboard running. It reuses the existing Mac demo
TLS certificate and reads the same `~/.config/doctutorials/demo-live-sessions.sqlite3`
file. Enter a unique pairing secret of at least 20 characters privately.
The terminal prints the certificate SHA256 fingerprint. On the Mac:

```bash
curl -fsSL https://raw.githubusercontent.com/vinodkumar-Hegde/doctutorials-zoom-suite/main/windows/central-controller/mac_session_bridge.py -o "$HOME/Downloads/DocTutorialsDemoReady/doctutorials-live-demo/mac_session_bridge.py"
python3 "$HOME/Downloads/DocTutorialsDemoReady/doctutorials-live-demo/mac_session_bridge.py"
```

Keep that Terminal window open; allow incoming port 8444 from your Windows
recording PC **only**. Mac private LAN IP can usually be shown with `ipconfig
getifaddr en0` (or check System Settings > Network). Neither the bridge nor
Windows pairing uses your Meeting SDK client secret.

**On Windows**, from the updated Controller folder run:

```powershell
.\pair-mac-sessions-windows.bat
```

Enter the Mac LAN IPv4 address, the exact certificate fingerprint printed by
Mac, and the same pairing secret (hidden). The Windows client verifies the
certificate SHA256 **before** sending the pairing secret. The pairing is saved
per Windows user in `%LOCALAPPDATA%\DocTutorials\session-feed.json`; keep that
file and user profile private. A production deployment should use Windows
Credential Manager / DPAPI rather than this development-only file.

Refresh `http://127.0.0.1:8780` after pairing. The Windows app checks for
assigned sessions every few seconds. It refuses stale data or connections
without a matching certificate. The **Prepare channel** action pre-fills the
session metadata in the selected channel. A configured recording source is
still required and **no Zoom capture is initiated by the schedule feed**.

## Zoom recording support boundary

Visual Studio C++ is installed on the Windows workstation and is a compiler,
not a Zoom SDK. The Zoom **Plugin SDK** is different from the **Meeting SDK**,
which has raw video/share/audio callbacks. Zoom's current Windows Meeting SDK
get-started documentation restricts bot/unattended uses; eligibility, meeting
access and recording permissions must be verified before an automated SDK
adapter is deployed. Zoom **RTMS** is an alternative media feed but requires
RTMS credits. This module does not pretend to connect to either. See:
https://developers.zoom.us/docs/meeting-sdk/windows/get-started/download/
https://developers.zoom.us/docs/meeting-sdk/windows/default-ui/advanced-features/raw-data/
https://developers.zoom.us/docs/rtms/

## Real Windows media source trial (not Zoom SDK)

Copy `config.windows-example.json` to the Git-ignored `config.json` and configure the Windows capture source, independent audio source, local SSD folder and NAS destination. First verify one authorized short meeting before enabling additional channels. Then use `start-recorder-windows.bat`.

The current Windows capture example uses FFmpeg `gdigrab` to capture configured portions of a visible Zoom window, and optionally WASAPI loopback for audio. **It will not reliably isolate four Zoom meetings on one Windows desktop.** The Zoom Meeting SDK raw-media adapter, automatic joins, central session orchestration and four real Zoom-channel acceptance tests remain unimplemented.

Never commit real meeting links, credentials, recordings or `config.json`. Only authorized classes should be recorded, with required consent and permissions.
