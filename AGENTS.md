# Working instructions for AI and human contributors

This file is the persistent project instruction set. Read `README.md` and all relevant `docs/` files before proposing or changing implementation.

## Rules
1. Treat `docs/01-PRODUCT-REQUIREMENTS.md` as the baseline for **confirmed** user requirements and `docs/11-RISKS-DECISIONS.md` as the decision/uncertainty register.
2. Never assume a capability exists because it is desirable. For each Zoom SDK/REST/webhook/participant permission, verify it against current official docs and a runnable proof of concept. Update `docs/13-OFFICIAL-REFERENCES.md` with the exact link.
3. Never imply Zoom native local recording is controllable from a REST recording API or that a cloud webhook represents local-recording status.
4. Keep all four licensed Zoom host accounts managed by DocTutorials. Faculty never receive their credentials.
5. Separate the cloud-backup pipeline from local recording; show independent health and status.
6. All four sessions must remain isolated: one channel's failure, pause, or stop must never affect another.
7. Treat Apple ReplayKit user confirmation as mandatory; do not attempt to bypass platform privacy controls.
8. Default to least-privilege OAuth. Keep secrets server-side; use encrypted credential storage. Never log or commit tokens, unique panelist links, access keys, recordings or student data.
9. Show operator-visible states and acknowledgements. Never mark a recording as started/saved/uploaded until independently verified.
10. Handle errors, idempotency, retries, webhook signature validation and replay protection, monitoring, and safe cleanup.
11. Before coding a major module, write a clear acceptance test and identify blocking feasibility dependencies.
12. Every work session: update `docs/SESSION-NOTES.md`, `docs/10-ROADMAP-ACCEPTANCE.md` and ADR/risk entries as appropriate.
13. Changes affecting architecture require a written ADR, reviewed before implementation.
14. Do not edit existing live/production Zoom settings, delete cloud recordings, or deploy production automation without explicit operator approval and rollback instructions.

## Engineering defaults (proposals, subject to review)
- Backend: Python FastAPI; PostgreSQL; background queue (e.g. Redis/RQ or Celery); HTTPS.
- Admin/faculty portal: TypeScript/React.
- iPad: Swift/SwiftUI, Zoom Meeting SDK, ReplayKit Broadcast Upload Extension.
- Windows worker: C++ Zoom Plugin SDK adapter + Windows service/controller, with supervised interactive client session where required.
- NAS sync: checksum verification, atomic copy/rename, retry and reconciliation.

## Work order (updated by operator 2026-11-14)
**Accepted priority override (ADR-016):** Backend Basic sandbox Meetings GET/auth PoC already PASSED → **custom iPad SwiftUI + Meeting SDK + ReplayKit full-screen sharing in a Basic sandbox Meeting (ACTIVE)** → faculty authorization/scheduling + validated iPad teaching experience → webinars only on separate approval after Meetings success → **Windows centralized local recording and four-channel scale LAST**, followed by integrated archive/production acceptance as applicable. Preserve the Windows Gate 3 evidence and keep its SDK claims unverified; do not resume Windows development until instructed.

App code must distinguish a UI demo from actual SDK meeting join and full-device broadcasting. Keep the system broadcast picker unavailable until observed Zoom meeting state, Zoom share permission and user privacy acknowledgement, and require Apple OS-level user confirmation.