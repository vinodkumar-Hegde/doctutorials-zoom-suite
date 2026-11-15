# DocTutorials Windows Zoom Desktop capture — first-meeting verification build

**No RTMS, OBS app, browser capture, Zoom Cloud Recording or Mac relay.** This is a separate path from the optional RTMS prototype. It uses the **Zoom Workplace desktop app on Windows** as the meeting viewer and **FFmpeg GDI window capture + Windows WASAPI speaker loopback** for the recording, with the existing branded picture-in-picture compositor and Storage Center/NAS workflow.

## Status — read before operating

This is **operator-assisted**, *not production verified*. The source and offline unit tests are available. **No Zoom meeting has yet been joined or recorded on the user's Windows machine by this build.** Automatic cross-computer detection of the faculty pressing Start is *not implemented*. For one class, the operator opens the assigned Zoom meeting in the Recording Center and checks the visible screen/audio before capturing. Only after a verified Zoom join and 5-minute real class recording should an auto-start signal from the Windows-hosted Faculty service be connected. The four-channel scheduler is not proof of four isolated Zoom desktop app instances/audio feeds.

The standalone original Admin database contains `meeting_id` and `meeting_passcode`, but the **schedule-only Windows export deliberately omits both**. The new Zoom desktop mode requires a **one-time private, offline migration** of the meeting-join records (not manual retyping). For all future changes to be automatic, the authoritative Admin/Faculty backend needs to run on the Windows service; the existing Mac-only Admin server is not a long-term source of live start events.

## One-time private migration, no credentials in chat

On the **Mac that holds the existing original Admin database**, after obtaining `export_private_zoom_registry.py` from this same GitHub directory, run:

```bash
python3 "$HOME/Downloads/export_private_zoom_registry.py"
```

This creates `~/Downloads/DocTutorialsPrivateZoomRegistry.sqlite3`, containing existing sessions' meeting IDs and passcodes. **This is confidential**. Transfer by approved encrypted/secure channel or offline drive to **Windows Downloads**, never email it publicly, commit to GitHub, or attach in chat. On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.config\doctutorials" | Out-Null
Copy-Item "$HOME\Downloads\DocTutorialsPrivateZoomRegistry.sqlite3" "$HOME\.config\doctutorials\private-live-sessions.sqlite3" -Force
```

Delete the two Downloads transfer copies after checking that the trusted Windows-local private file works; retain the Mac original database securely. The observer reads the Windows-local private file **read-only** and only after matching session ID, faculty ID and schedule times against the publicly imported class assignment. Meeting numbers/passcodes are never returned to the dashboard. Do not publish that private file.

## Running the first authorized Windows meeting

In **Windows PowerShell**, after `git pull --ff-only`:

```powershell
py -3 -m pip install soundcard numpy
cd "$HOME\doctutorials-zoom-suite\windows\central-controller"
.\start-zoom-desktop-windows.bat
```

This reuses existing `config.json` created in the earlier readiness step and all existing Storage Center files. `soundcard` and `numpy` provide the **Windows default speaker** WASAPI loopback. The Zoom Workplace desktop app and Windows speaker output must be present. Open `http://127.0.0.1:8780` in the Windows browser and sign in.

1. While the existing class is in its scheduled time window, click **Open assigned Zoom** on the imported class card. Zoom's historical `zoommtg://` desktop URL scheme is **not officially guaranteed** and may require confirming the desktop handoff or joining the meeting manually. The code never returns the private Zoom URL to the web UI.
2. Join the meeting in the Zoom desktop app; select **Join Audio / Computer Audio**, make the faculty's Goodnotes share visible, and place the faculty camera tile in the top-right of that Zoom meeting window. Admit the Recording Center observer if required. Grant institutional recording consent/notice.
3. Click **Preview Zoom window**. The captured image is from the actual Zoom desktop window handle, never a browser screen-capture API or the whole desktop. Verify screen, tile and layout. Then click **Capture Zoom window** to start FFmpeg. The camera picture-in-picture is a **top-right crop estimate** and is **not identity-locked** to the faculty until validated.
4. When the class ends, click **Stop & save MP4**. Check Storage Center for H.264/AAC MP4 and verify sound, camera, Goodnotes content, and A/V sync. No automatic source-to-faculty identity verification is claimed.

Zoom may show launch, admission, audio prompts or waiting rooms; this mode **does not bypass** them. The initial zoommtg URL handler is historically used but not officially supported by Zoom for every client/version: https://devforum.zoom.us/t/zoom-url-scheme-query/50832 . FFmpeg's supported window handle source: https://www.ffmpeg.org/ffmpeg-devices.html#gdigrab .

## Deliberate restrictions

- Desktop mode must be started with `--config config.json --desktop`. Demo mode remains **TEST MEDIA — NOT ZOOM**. No RTMS entitlement is required.
- A **single visible** Zoom meeting window matching a Zoom process is required. Zero or multiple are blocked. Minimized or tiny windows are rejected. It is operator-verified that this is the correct meeting; the computer cannot yet cryptographically prove Zoom participant identity from pixels.
- Only **one** desktop capture at a time. The Windows default audio output mixes all programs; four concurrent classes would cross-contaminate audio. Multi-meeting isolation needs separate OS user sessions/VMs and independent sound devices (or a different documented Zoom media interface). Zoom's official multi-meeting policy additionally restricts simultaneous desktop joining: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0067266 .
- A **current** private meeting registry is necessary; stale or mismatched sessions are rejected rather than guessing a meeting. Existing original Mac Admin changes are not magically synchronized to Windows.
- Zoom meeting-window video tile may move or disappear when screen sharing, recording, or changing Zoom layout. The screenshot preview is the first acceptance check; no reliable picture-in-picture until validated for the actual Zoom version/display arrangement.
- Neither `ZoomDesktopController.status()` nor the HTTP API returns meeting IDs, passcodes or join links. The local service binds to **127.0.0.1 only**.
- Zoom does not reliably expose a faculty-start signal to this local window recorder. Future true hands-free joining needs a trusted event emitted from the **Windows-hosted** DocTutorials Faculty start action; this release does not claim it.

Tests: `py -3 -m unittest discover -s tests -v`. Offline tests verify private mapping, gatekeeping, Windows source construction, authenticated operator actions, preview and safe failure, but they **do not** verify Zoom rendering on a real Windows workstation.


## Automatic mode (no per-class operator buttons)

For the experimental ordinary Zoom `meeting.started`/`meeting.ended` WebSocket
event path, see `README-ZOOM-AUTO.md` and `start-zoom-auto-windows.bat`.
This mode does **not** require RTMS. It is separate from this operator-assisted
verification mode and is limited to one window/audio channel pending acceptance.
