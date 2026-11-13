# System Architecture — v0.1

## Services
| Component | Proposed technology | Description |
|---|---|---|
| Auth & session API | FastAPI + PostgreSQL | Faculty login, schedules, Zoom user mapping, recording job state |
| Zoom connector | Server-to-Server OAuth + signed webhooks | Account-level host/session discovery, start/end events, cloud recording lifecycle |
| Faculty web portal | React/TypeScript | Assigned sessions, native laptop join, recording health |
| Faculty iPad | SwiftUI + Zoom Meeting SDK + ReplayKit | Join scheduled Zoom webinar, present iPad content |
| Windows worker controller | Native application + Zoom Plugin SDK, feasibility-gated | Authorized per-host Zoom Workplace control and local capture |
| Archive service | Background worker + checksum/NAS | Finalization, local/cloud transfer, verification, metadata |
| Operator dashboard | Web app | Four-channel telemetry, alerts, recovery, audit |

## Trust boundaries
- Frontends never contain Zoom OAuth client secrets, Server-to-Server OAuth credentials, cloud file download bearer tokens, host password, or backend signing keys.
- Backend has account-scoped access only as required; separate scopes for list/read, scheduling write, and recording download.
- Windows recorder agents authenticate to DocTutorials backend with rotated per-worker credentials and only receive scoped jobs.
- iPad Meeting SDK receives short-lived, backend-issued SDK signature/authorization; no long-lived SDK secret on device.
- NAS service account has least-privilege access; no credential shared to faculty devices.

## Four-way isolation
A `zoom_host_account` maps to one active `recorder_channel` at a time. During a concurrent session window, create one job per host/user/session combination. Workload isolation needs empirical verification: a Windows machine may run four separate operating-system environments, or the fallback is four physical mini-PC workers under one dashboard.

## Session lifecycle
1. Admin assigns a host user, faculty, course, subject, schedule, webinar/meeting ID.
2. Authorized host process starts webinar, or an operator performs the startup when unattended startup is not supported.
3. Zoom emits meeting/webinar started webhook; backend validates signature and stores idempotently.
4. Recorder worker must be verified **joined, privileged, healthy** before local recording command.
5. Cloud recording automatically starts by Zoom policy when supported; local recording starts by separate agent path.
6. Faculty laptop/iPad supply video, microphone, and share.
7. Recording ends, converts, and is checked before archival.
8. Cloud `recording.completed` webhook kicks off a separate authorized download/archive job.

## Important open feasibility questions
- Can a Windows Plugin SDK controller fully start/stop and confirm local recordings for a host client, including webinars? Verify exact SDK version and APIs.
- Can four independent VM-hosted Zoom Workplace instances on one machine record concurrently with stable media and audio capture?
- Are Webinar host startup and recording actions automatable without unintended account/device conflicts?
- How will iPad SDK participant join obtain the correct webinar panelist authorization without a Zoom host credential?
- Does each Zoom host account's recording layout produce intended shared screen plus faculty video?

## Fallback decision tree
- First: native Zoom desktop + Plugin SDK managed host-recorder worker.
- Second: separate Windows PCs (physical isolation) if virtualization fails.
- Third: evaluate RTMS ingest/composition/cost/licensing and SDK policy if native recording control is unsupported. RTMS does **not** automatically duplicate Zoom's native MP4 layout.

See `docs/11-RISKS-DECISIONS.md` for decision records.
