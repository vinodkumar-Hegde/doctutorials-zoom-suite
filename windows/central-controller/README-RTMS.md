# DocTutorials Zoom RTMS proof — Windows (unverified live capture)

**Do not use this prototype to record production classes.** The known working item remains four independent synthetic test workers and the imported, automatically planned class schedule. RTMS real packet transport has NOT been tested with the operator's Zoom account or on Windows.

## What this source code adds

- A Windows-native **outbound** authenticated Zoom Event WebSocket client using the published, transport-level RTMS protocol via Python's `websocket-client` library. It listens for Zoom `meeting.rtms_started` and `meeting.rtms_stopped`, performs HMAC-signed RTMS signaling/media handshakes, and requests three independent streams: mixed PCM audio (L16 16kHz mono), active-speaker H.264 video (25 fps), and H.264 screen share (25 fps). The App's Zoom Event WebSocket URL and app ID/secret are environment variables, never committed.
- An inbound RTMS media-track collector (NOT a synthetic recorder source) that preserves `.h264` and `.s16le` media tracks in local staging, validates packet type and base64, and rejects unknown codecs.
- After a **genuine Zoom RTMS stop event**, FFmpeg combines the three tracks with a branded teaching-screen + camera PIP + footer layout. Only `ffprobe`-verified H.264/AAC MP4 is imported into the existing local Storage Center and optionally checksummed/copied to NAS. Invalid or incomplete media is NOT silently treated as recorded; unprocessed staging survives for diagnosis.
- Automatically uses existing Admin assignments. Because the exported Admin schedule does NOT carry Zoom meeting identity, automatic matching is allowed only if **exactly one** imported class has an active schedule. Two or more simultaneous classes are deliberately rejected until a secure authoritative session-to-Zoom meeting mapping exists; no manually typed class details or guesswork.
- `--rtms` is rejected in `--demo` mode. `Run TEST MEDIA` still cannot be passed off as Zoom.

## Hard limitations / acceptance gate

- **Not end-to-end verified:** no live RTMS entitlements or data have been provided to this process; no Windows RTMS handshake, no real synchronized 1-hour teaching recording, and no four-channel RTMS capacity or NAS test yet. Zoom RTMS is metered and requires a separate approved RTMS-capable app, Zoom Developer Pack credits, RTMS scopes/event subscription and applicable participant notice/host approval. The existing S2S Basic sandbox is not a substitute. No Zoom account settings were changed.
- RTMS video is *active speaker*, **not yet a guaranteed faculty participant camera**. Identity-stable participant selection and full Goodnotes screen quality still require acceptance work.
- The first-pass compositor assumes 25 fps and contiguous H.264/PCM tracks. Timestamps are retained for diagnostics, but buffer-delay adjustment, mute/screen-off filler, frame jitter/reconnection, media loss, stream-time alignment, 8-hour duration reliability, and hardware capacity have **not** been solved or production-tested. In particular, output may have A/V drift; do not distribute until independently inspected.
- Python `websocket-client` must be installed (in addition to existing Pillow/FFmpeg). The separate Zoom RTMS SDK binary is not used; official Zoom samples document the native WebSocket protocol. No macOS relay or public inbound port is required when using Zoom Event WebSocket subscriptions.
- Do **not** reuse normal Meeting SDK Client Secret or S2S Account ID as this RTMS-specific app's credentials. Never paste or upload credentials to ChatGPT/GitHub, or save them into a project file.
- An external/remote meeting must be captured only after valid authorization and recording notice; stop conditions and stream auto-start must respect Zoom host controls and current policy.

## Developer-only activation (after RTMS permissions and credits are confirmed)

On the **Windows** recording PC, copy `config.windows-example.json` to a local ignored `config.json`; set your Windows storage root and NAS target; leave existing channels `configured:false` until you have independently established valid media sources. This RTMS collector does not require configuring GDI/DShow channels.

Create a new PowerShell session and set these three variables via your trusted local enterprise secret manager/session mechanism (do not commit; process environment only): `ZOOM_RTMS_CLIENT_ID`, `ZOOM_RTMS_CLIENT_SECRET`, and `ZOOM_RTMS_EVENT_WSS` (the Zoom-authorized Event WebSocket endpoint). Do not paste secret values into chat. Install the one Python library if needed:

```powershell
py -3 -m pip install websocket-client
cd "$HOME\doctutorials-zoom-suite\windows\central-controller"
.\start-zoom-rtms-windows.bat
```

The standard `start-demo-windows.bat` intentionally **does not** activate Zoom RTMS. This is the safer default. Test first against one authorized sandbox Meeting; verify screen, audio, active-speaker video, encoding and timestamp alignment. No RTMS connection will occur until a distinct authorized Zoom App with the proper scopes/credits is configured. Do not run on four simultaneous classes until deterministic Zoom meeting-to-Admin session mapping exists.

## Source references

- Zoom Meetings RTMS overview/credits: https://developers.zoom.us/docs/rtms/meetings/getting-started/
- Native RTMS WebSocket protocol samples: https://github.com/zoom/rtms-samples
- Zoom RTMS media codecs/timestamps: https://developers.zoom.us/docs/rtms/meetings/media/
- Zoom Meeting SDK usage policy: https://developers.zoom.us/docs/meeting-sdk/windows/get-started/download/
