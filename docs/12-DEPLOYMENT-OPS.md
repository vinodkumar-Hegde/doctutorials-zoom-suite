# Deployment and Operations Runbook — Outline

## Environments
- Development: isolated test Zoom host/user and simulated data; no real learners.
- Staging: test webinar, iPad, laptop, single Windows worker; safe recordings.
- Production: four Zoom host identities, four workers, cloud backup, monitored NAS.

## Release process
1. Merge reviewed changes to protected branch, run static checks and tests.
2. Deploy backend to staging; configure secrets through vault.
3. Run webhook/auth/worker health tests and iPad real-device checks.
4. Pilot on one host; verify cloud and local recordings, then scale.
5. Maintain rapid rollback to native Zoom recording + manual office operator.

## Observability
- Alerts for schedule-start missed, Zoom webinar not live, worker offline, local recording not started, media lost, conversion stuck, file mismatch, NAS full, cloud recording missing, download failure, 4-channel capacity overload.
- Channel telemetry: host alias, session UUID, current Zoom meeting UUID, observed recording state, CPU/memory/disk, latest media/frame heartbeat if supported, upload status.
- Daily reconciliation: list expected sessions, local assets, cloud assets; alert mismatches.

## Operational safety
- Always obtain recording consent per applicable rules; visible recording notice.
- Do not delete cloud backup until archive copy verified and policy permits.
- Do not stream raw recording data or personally identifying participant information in logs.
- Keep credentials and signed invite URLs out of issue descriptions, PRs, commit history.

## Recovery drills
- Windows reboot during live class; host login failure; iPad reconnect; Zoom network drop; cloud processing delay; NAS unavailable; worker disk fills; cloud quota exhausted.
- For each failure, identify affected job, preserve partial files, notify operator, reconcile archive and update incident notes.
