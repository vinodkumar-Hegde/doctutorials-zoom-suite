# Windows automatic reservation of imported Admin sessions (v5)

The Windows controller now computes a stable, read-only plan from the **already-imported** DocTutorials Admin `sessions` table. A session during its time window appears on the first available of four channels; sequential classes reuse slots and a fifth overlapping class is explicitly flagged. No one must re-enter course/subject/topic/faculty. This version does **not** copy, delete, or edit the Admin database.

The dashboard uses two independent assertions:

- **AUTO-RESERVED:** scheduling metadata was assigned to a channel from existing Admin data; this does not indicate Zoom presence.
- **Zoom media NOT CONNECTED:** the controller has not joined or verified the real meeting audio/video/screen-share stream. `start-demo-windows.bat` remains synthetic test media; it must not record a real imported class.

The protected `POST /api/start-assigned` endpoint accepts `{ "sessionId": "...", "consentConfirmed": true }` and looks up the actual imported metadata and channel. It refuses unimported sessions, outside-window classes, fifth overlapping classes, and synthetic or file inputs. **It does not join Zoom, identify the actual media source, or prove participant notice; the operator must verify the configured source and permissions.** The legacy manual `/api/start` refuses real imported session IDs to prevent labeling test media as real classes.

## Update your existing Windows repository

Stop the running controller with Ctrl+C (do not stop mid-recording), then in Windows PowerShell:

```powershell
cd "$HOME\doctutorials-zoom-suite"
git pull --ff-only
cd .\windows\central-controller
.\start-demo-windows.bat
```

Open `http://127.0.0.1:8780` and hard-refresh (Ctrl+Shift+R). Your previously imported `~/.config/doctutorials/demo-live-sessions.sqlite3` is still used; no re-export and no Mac bridge. The first currently scheduled imported class should be visible on Channel 1 as a reservation, with any other classes assigned to separate channels where their windows overlap. All four slots will continue to say TEST MEDIA until real inputs exist.

## Zoom media prerequisites, not yet met

For an unattended centralized media-capture design, Zoom's current Meeting SDK documentation says it is intended for human meeting participation and recommends **RTMS** for realtime media access. Zoom RTMS for Meetings can provide audio, video, and screen share but requires a separately authorized General app, subscribed events/scopes, and Zoom Developer Pack credits. No RTMS production credentials, real streaming session, channel adapter, four-concurrent-channel live capture, NAS deployment, or real Zoom MP4 validation have been proven on this Windows PC. Do not enable automated production recordings based on these reservations alone.

Official: https://developers.zoom.us/docs/meeting-sdk/windows/ ; https://developers.zoom.us/docs/rtms/meetings/getting-started/

## Test

```
py -3 -m unittest discover -s tests -v
```

This version's tests cover deterministic non-overlapping automatic reservations, authenticated status, source/consent rejection, and use of imported metadata for configured inputs. Unit tests run with synthetic or fake media; they do not establish Zoom media capture.
