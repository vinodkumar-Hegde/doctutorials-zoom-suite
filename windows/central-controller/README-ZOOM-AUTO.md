# DocTutorials automatic Zoom Workplace capture: Windows event-driven prototype

**Goal:** Faculty (host) starts an assigned Zoom meeting. Zoom emits its ordinary
`meeting.started` account event, the Windows Recording Center looks up that
Zoom meeting ID privately, requests Zoom Workplace to join, waits for a NEW
visible Zoom meeting window, begins FFmpeg capture of the window + Windows
speaker loopback, then finalizes the branded H.264/AAC MP4 to Storage Center
when Zoom emits `meeting.ended`.

This is **not** RTMS, Zoom Cloud Recording, browser screen capture, OBS, or
an integration with the Mac. No per-class button/confirmation is required.
It is also **not a proven hands-free deployment**: Zoom can present guest join,
authentication, waiting-room, audio, OS link handler or recording-notice
prompts. Zoom desktop window detection cannot prove that the faculty camera
or Goodnotes share is visible. A real Windows meeting acceptance test is required.

## One-time setup (not repeated for each class)

1. Keep the original **private Admin meeting registry** under
   `%USERPROFILE%\.config\doctutorials\private-live-sessions.sqlite3`.
   It must match the public Admin session by session ID, faculty, course,
   subject and topic. *Changes of the class time no longer require re-export*,
   but changes to the actual Zoom meeting ID still do. No Zoom secrets may be
   committed or pasted into chat.
2. In the **existing Zoom server-to-server OAuth or General app** (not RTMS),
   enable **Event Subscriptions → WebSocket → Meeting started and ended**.
   Obtain its generated `wss://ws.zoom.us/...` endpoint. This is a normal
   Zoom account event subscription, not media streaming or paid RTMS.
   Zoom events are account-bound: the faculty host must belong to the app's
   subscribed account (or use an approved app). The Windows PC uses an
   outbound connection; no public listener is needed.
3. Use the **DocTutorials-Backend event subscription** and its Client ID, Client Secret and WebSocket URL. Keep them in the Windows PowerShell process environment:
   `ZOOM_EVENTS_CLIENT_ID`, `ZOOM_EVENTS_CLIENT_SECRET`, `ZOOM_EVENTS_WSS`.
   **Actual Windows diagnostic evidence (15 November 2026):** `client_credentials` returned a token and connected to the WebSocket; `account_credentials` returned HTTP 400. Therefore the event WebSocket receiver uses `grant_type=client_credentials`, not the standard S2S account grant. The Account ID is not required for this listener. This distinction applies to Zoom's event WebSocket and does not change ordinary Server-to-Server REST OAuth usage. Do not store secrets in a .bat, config.json, GitHub or browser.
4. Obtain and document faculty/attendee meeting recording notice and permission
   as applicable. For a deployment where every enrolled class has the required
   authorization and notice, set `DOCTUTORIALS_AUTO_NOTICE_CONFIRMED=YES`
   through Windows local configuration. This **does not override** Zoom host
   settings, waiting rooms or recording consent requirements.
5. Ensure Zoom Workplace is installed on the dedicated Windows PC and the
   recorder account can join the assigned meeting without interactive prompts.
   Use the same existing `config.json` with local Storage Center and FFmpeg.
   Audio comes from the default Windows speaker, so only **one meeting** may
   be recorded at a time until audio/video isolation is built and tested.

Start once when Windows starts (e.g., using a supervised Windows service or
Task Scheduler in an interactive desktop user session):

```powershell
cd "$HOME\doctutorials-zoom-suite\windows\central-controller"
.\start-zoom-auto-windows.bat
```

Keep the recorder process alive through class times. No manual Open or Capture
click is needed during the class. The dashboard shows a sanitized
`desktopAutomation` phase such as `waiting_for_zoom_event`, `joining`,
`capture_started_unverified`, `saved_to_storage_center`, or `blocked`.

**Important safety limits:** The observer refuses multiple or pre-existing Zoom
meeting windows; refuses meeting IDs absent from the private Admin DB;
refuses non-unique class mapping and overlapping desktop workers; and will
not start without the institution's explicit recording-notice policy. The
browser does not receive Zoom numbers or passcodes. Zoom Desktop protocol
`zoommtg://` is historically supported but not guaranteed by Zoom for all
Zoom versions. FFmpeg `gdigrab` window capture may show blank frames with
hardware acceleration or Windows display/session changes. Real 5-minute
capture and stop/storage acceptance tests have NOT yet been performed.

For **four simultaneous meetings**, a single Windows Zoom desktop user and
one shared speaker output are insufficient. Zoom's simultaneous meeting join
setting must be enabled where eligible, and DocTutorials needs four separately
isolated app/session/audio capture environments. The prototype deliberately
keeps one channel active to prevent cross-class mixing.

Sources: https://developers.zoom.us/docs/api/meetings/events/ ;
https://developers.zoom.us/docs/api/websockets/ ;
https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0067266 ;
https://ffmpeg.org/ffmpeg-devices.html#gdigrab

## Connection diagnostic (does not join or record meetings)

If the Windows dashboard shows \`event_connection_unavailable\`, first verify the
**DocTutorials-Backend** Server-to-Server OAuth app has completed **Activation**
and the WebSocket subscription includes Meeting Started and Meeting Ended.
Zoom will not issue regular Server-to-Server access tokens for an inactive app.

Stop the existing Windows automatic recorder with Ctrl+C to avoid competing
WebSocket connections, then run from the same Windows PowerShell session:

\`\`\`powershell
cd "$HOME\doctutorials-zoom-suite"
git pull --ff-only
cd .\windows\central-controller
.\check-zoom-events-windows.bat
\`\`\`

This check reports only SET/MISSING, OAuth HTTP status, and WebSocket handshake
status, never access tokens, account IDs, passcodes or the credential-bearing URL.
It tries both grant types because the Zoom WebSocket API docs document
\`client_credentials\` whereas generic Server-to-Server OAuth documentation
describes \`account_credentials\`. A successful diagnostic connection does NOT
prove a real Zoom meeting can be joined or recorded. Test during a NEW active
class schedule; previous class sessions do not reactivate automatically.

## Windows event connection correction (2026-11-15)

The operator's preflight showed `Zoom OAuth client_credentials: PASS`, `Zoom OAuth account_credentials: HTTP 400`, and `Zoom WebSocket using client_credentials: CONNECTED`. The listener and Windows launcher now use only the proven event WebSocket grant. A connected event socket displays `event_connected_waiting_for_meeting`; this is transport readiness, not proof of meeting capture.

Run `git pull --ff-only` and restart `start-zoom-auto-windows.bat` from the SAME PowerShell session containing the prior Zoom environment variables. Use a new future Admin class for the first authorized end-to-end test; the 18:15–20:15 session already ended and cannot trigger an active channel now.


## WebSocket lifetime correction (2026-11-15)

The Windows diagnostic verified an initial OAuth/WebSocket handshake, but the
operator later observed `event_disconnected`. Zoom documents a JSON
`{"module":"heartbeat"}` every 30 seconds; the event receiver now sends it
on open and every 20 seconds, without a competing 25-second WebSocket Ping +
10-second Pong timeout. A sanitized close code or transport-error class is
shown in the dashboard if the connection still drops. An initial diagnostic
handshake is not proof of a long-lived connection; run a live Windows test.

**Only one active event WebSocket connection is allowed per Zoom
subscription.** Do not run `check-zoom-events-windows.bat` while the
auto-recorder is running because the check may replace that connection.
Close all older listeners before launching the new one. A gap in WebSocket
connectivity can permanently miss Zoom meeting-start events; only events
received while connected are delivered. The old scheduled NEET SS class is
already past and will not auto-trigger.
