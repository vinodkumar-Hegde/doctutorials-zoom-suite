# Windows Recorder — Four Independent Channels

## Current intent
One Windows workstation (user says hardware meets earlier recommended sizing) supports at least four independent sessions from different Zoom host users. Each Zoom host user is mapped to a distinct recording worker and isolated output directory.

## Candidate architecture A — isolated Windows environments
- Four separate Windows VM/user environments; each runs an authorized signed-in Zoom Workplace client (exact account/host identity plan to test).
- Each VM runs a local native Plugin SDK controller with a secure command link to DocTutorials backend.
- One worker per active host account, one webinar per worker.
- Storage volume reservation and quotas per channel; independent logging/health and process supervision.
- Verify interactive desktop, audio device, media quality, GPU acceleration/virtualization, Zoom policies and client behavior under concurrent load.

**This is a candidate, not a verified deployment.** A recommended hardware target (e.g., 16+ modern cores, 64 GB RAM, NVMe) is not proof of four reliable Zoom virtualized recorders. Test on the user's exact hardware.

## Candidate architecture B — four physical recording clients
If four VMs are unsupported or unreliable, use four Windows mini-PCs (one per host) managed from one dashboard and archive to the same NAS. This costs more hardware but reduces virtualization uncertainty.

## SDK proof-of-concept order
1. Confirm Windows Zoom Workplace version >= 7.0.2 and matching Plugin SDK.
2. Authenticate native Plugin SDK against one actual signed-in Zoom client.
3. Verify current meeting/webinar context and host identity.
4. Verify the **actual supported API and privileges** for start, stop, pause and resume local recording; do not assume all are available.
5. Record a live webinar including laptop webcam/audio and iPad broadcast; inspect output.
6. Stop and confirm Zoom conversion, MP4 presence, file health and duration.
7. Repeat with two simultaneous workers; then three; then four. Monitor CPU, memory, disks, media quality and sessions.
8. Document rollback and manual startup for host/auth failures.

## Recorder-worker contract (proposal)
- `POST /recorder/channels/{channelId}/prepare` — idempotent prepare
- `POST /recorder/channels/{channelId}/start` — start when ready
- `POST /recorder/channels/{channelId}/pause|resume|stop` — capability-gated
- `GET /recorder/channels/{channelId}/status` — actual state, not desired state
- Worker emits signed events: joined, unauthorized, recording_started, recording_paused, stop_ack, file_ready, checksum_ok, error.

## Archive contract
Local SSD is primary write target; only fully converted, verified MP4 transferred to NAS. Preserve sidecars and raw Zoom recovery format while incomplete. Use checksums, retries, atomic file promotion, and manifest.

Official: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/
