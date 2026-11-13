# Recording Workflows

## Mode A — Laptop + iPad
1. Scheduled under one of four Zoom host users.
2. Authorized office host starts the webinar and worker becomes ready; webinar practice sessions are not the final live phase.
3. Faculty joins from native Zoom laptop as authorized panelist (camera+mic); iPad joins with a separate authorized panelist identity or verified SDK workflow.
4. iPad is muted and camera off; faculty starts ReplayKit system broadcast and moves to Goodnotes/other content.
5. Zoom sends shared content and faculty video/audio to attendees.
6. Zoom cloud recording starts automatically when webinar is live and settings allow.
7. Assigned Windows local-recorder job starts separately after host, join/permission and media readiness are verified.
8. Worker finalizes local output; archive service verifies and copies to NAS. Zoom cloud completion is processed independently.

## Mode B — Laptop only
Same sequence without iPad. Faculty uses laptop to share screen and provide webcam/audio.

## Recording state machines
Local: `SCHEDULED → PREPARING → JOINED → READY → RECORDING → [PAUSED ↔ RECORDING] → STOPPING → CONVERTING → VERIFYING → ARCHIVED`; exceptional: `ERROR`, `RECOVERY_PENDING`, `MANUAL_REVIEW`.

Cloud: `EXPECTED → STARTED_OR_DETECTED → PROCESSING → AVAILABLE → DOWNLOADING → VERIFIED → ARCHIVED`; exceptional: `MISSING`, `FAILED`, `RETRYING`.

Never infer local recording state from cloud webhooks. Never infer saved MP4 merely from a successful start-command response.

## Trigger policy — requires proof
- Preferred reliability: recorder joins/prepares **before lecture**, local recording starts when authorized host/session is actually ready; capture first teaching frame.
- Faculty Start/Pause/Resume/Stop buttons send scoped backend jobs for local channel **if verified supported by Plugin SDK**.
- Faculty pressing Zoom's native **local** Record button on their laptop does **not** remotely record on the office Windows machine.
- `meeting.started`/`webinar.started` webhooks can trigger workflow preparation but delivery may lag; a separate readiness protocol prevents missed opening minutes.
- Cloud automatic recording is independent and should remain continuous as backup.

## Recording layout and archival
Test layout with active faculty video beside shared content, audio quality, presenter switching and iPad writing fidelity. Define naming strategy using non-PII session UUID and controlled course metadata. Save to local SSD, wait for conversion, verify duration/size/checksum, then archive through temporary file + atomic rename. Retain a machine-readable manifest.

## Failure handling
- Host not started: notify operator; don't fake start.
- Join/auth/permission failure: alert, retry safely, preserve cloud backup.
- Screen broadcast stops: alert faculty; local recording may continue with fallback camera view.
- Network/storage loss: preserve any partial Zoom format files; do not delete before recovery.
- Cloud processing delayed: show `PROCESSING`; download only after available.
