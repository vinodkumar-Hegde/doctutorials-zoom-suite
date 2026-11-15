# DocTutorials Windows Central Controller — use existing Admin assignments

This build **removes the duplicate Windows 'Assign Class' form**. The recorder dashboard reads the existing DocTutorials Admin/Faculty SQLite session format, without inventing new assignments or requiring the user to type class data again. It is **read-only** and displays only course, subject, topic, faculty ID, and start/end times. It does not transmit Zoom meeting IDs, passwords or meeting passcodes to the UI.

## Already installed on Windows

Stop the running controller with Ctrl+C. In Windows PowerShell:

```powershell
cd "$HOME\doctutorials-zoom-suite"
git pull --ff-only
cd .\windows\central-controller
.\start-demo-windows.bat
```

Open `http://127.0.0.1:8780` on the same Windows machine, then hard-refresh the browser and log in. **No reinstallation of Visual Studio, Python, FFmpeg or the Mac pairing bridge.** The existing four independent test channels and Storage Center remain.

## Where existing class assignments are

The original Mac Admin demo stores all sessions in `~/.config/doctutorials/demo-live-sessions.sqlite3` on **that Mac**. The Windows controller cannot see Mac files by itself. **One secure transfer** of schedule data is required; no permanent Mac/Windows connection. A snapshot is not automatically updated when classes change on the Mac.

A small script exports only the seven scheduling fields; **no Zoom meeting number, passcode or credentials**:

On the **Mac**, run from the downloaded Mac Terminal:

```bash
curl -fsSL "https://raw.githubusercontent.com/vinodkumar-Hegde/doctutorials-zoom-suite/main/windows/central-controller/export_existing_admin_schedule.py" -o "$HOME/Downloads/export_existing_admin_schedule.py"
python3 "$HOME/Downloads/export_existing_admin_schedule.py"
```

This creates `~/Downloads/DocTutorialsAdminSchedule.sqlite3`. Transfer that file to the **Windows** computer by an approved secure file transfer/USB (do not upload to public GitHub or ChatGPT). Assuming it is then in Windows **Downloads**, stop the running controller, and run in **Windows PowerShell**:

```powershell
New-Item -Type Directory -Force "$HOME\.config\doctutorials" | Out-Null
Copy-Item "$HOME\Downloads\DocTutorialsAdminSchedule.sqlite3" "$HOME\.config\doctutorials\demo-live-sessions.sqlite3" -Force
cd "$HOME\doctutorials-zoom-suite\windows\central-controller"
.\start-demo-windows.bat
```

This does **not** overwrite your original Mac database. The Windows controller reads that Windows-local file fresh each time the dashboard polls; changes made to this Windows file appear without restarting. For now, new changes saved only in the Mac Admin portal require another schedule-only export. The proper production solution will move the authoritative Admin and faculty service onto Windows, with the recorder reading its database directly. That move is not yet implemented.

## Accurate status and restrictions

- The schedule list is NOT live Zoom meeting presence or recording status.
- `start-demo-windows.bat` uses synthetic FFmpeg test media. The test button needs no manual class metadata.
- Real Zoom screen/faculty/audio capture, automatic joins, Zoom SDK/RTMS integration, four concurrent meetings, iPad-to-Windows faculty orchestration and production NAS verification are **not implemented/verified** in this build.
- The controller binds to `127.0.0.1:8780`. Do not expose it directly on the LAN or internet.
- The schedule-only export still contains faculty/class information; secure or delete the transfer copy according to your office policy.
- The obsolete `windows-admin-sessions.sqlite3` created by a previous prototype is **not deleted** and is **not used as a source for the dashboard**; no existing recordings are deleted.

Run tests in Windows with `py -3 -m unittest discover -s tests -v`.

## Updated: automatic session-to-channel reservations

Existing Admin session metadata now appears **on its automatically reserved recording channel** without a manual class form or any new export. This is a *schedule reservation*, not proof that a Zoom class is live or being captured. The demo still outputs only test media. See [README-AUTO-CHANNELS.md](README-AUTO-CHANNELS.md) for exact status, source checks and remaining Zoom RTMS integration requirements.

## Native outbound Zoom RTMS media spike — NOT live Zoom verified

The new optional `--rtms` mode has a first-pass direct Zoom Event WebSocket/RTMS media transport and track-to-branded-MP4 compositor. It does not use Mac, OBS, Zoom Cloud Recording, or Zoom Workplace local recording. **It has only been tested with offline generated packet fixtures, not with an authorized Zoom RTMS meeting.** It is not enabled by `start-demo-windows.bat`. See [README-RTMS.md](README-RTMS.md) before any account changes. It requires a separate enabled RTMS app, credits, scopes, participant notice, and an outbound Event WebSocket subscription. With the exported schedule alone, it can safely match **one** active class; multiple active meetings are blocked until the Admin backend stores a secure Zoom meeting identity mapping.
