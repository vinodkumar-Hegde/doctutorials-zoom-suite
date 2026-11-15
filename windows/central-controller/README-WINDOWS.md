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

## Real Windows media source trial (not Zoom SDK)

Copy `config.windows-example.json` to the Git-ignored `config.json` and configure the Windows capture source, independent audio source, local SSD folder and NAS destination. First verify one authorized short meeting before enabling additional channels. Then use `start-recorder-windows.bat`.

The current Windows capture example uses FFmpeg `gdigrab` to capture configured portions of a visible Zoom window, and optionally WASAPI loopback for audio. **It will not reliably isolate four Zoom meetings on one Windows desktop.** The Zoom Meeting SDK raw-media adapter, automatic joins, central session orchestration and four real Zoom-channel acceptance tests remain unimplemented.

Never commit real meeting links, credentials, recordings or `config.json`. Only authorized classes should be recorded, with required consent and permissions.
