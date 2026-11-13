# Product Requirements — v0.1

Updated: 2026-11-13. Requirements with `[CONFIRMED]` are from the project conversation; `[PROPOSED]` require implementation approval.

## Organization and hosting
- [CONFIRMED] One Zoom organization/admin controls **four configured host users** with meeting/webinar entitlements and varying participant capacities (illustratively 3000/1000/500/300; account-to-capacity mapping needs confirmation).
- [CONFIRMED] Each host user runs at most one active session at a time; different courses/subjects may run concurrently.
- [CONFIRMED] Target: **at least four simultaneous independent sessions**.
- [CONFIRMED] Office recording hardware runs Windows and is stated to meet earlier sizing guidance; exact CPU/RAM/network/audio virtualization details unverified.

## Faculty teaching
- [CONFIRMED] Faculty use laptops for camera, microphone, or full screen sharing.
- [CONFIRMED] Some faculty use laptop for video/audio plus iPad for note-taking and screen sharing.
- [CONFIRMED] Faculty must not receive Zoom host account usernames/passwords.
- [CONFIRMED] Build a branded DocTutorials faculty iPad application; faculty should be able to share Goodnotes/Notability/other apps using iOS screen broadcast after OS confirmation.
- [PROPOSED] Faculty sign in once to DocTutorials, see their assigned sessions, and join as webinar panelists by verified entitlement, without receiving reusable host credentials.

## Recording
- [CONFIRMED] Automatic **cloud** recording should be enabled by default across all four Zoom host users as a safety backup.
- [CONFIRMED] Windows office system should save **local** Zoom session footage, four at once.
- [CONFIRMED] Files should be organized by course/subject/topic/session and copied to NAS.
- [PROPOSED] An office worker is prepared before teaching begins and begins local recording automatically when host/session readiness criteria are met. Actual triggering and Plugin SDK behavior need proof.
- [PROPOSED] Cloud recordings are automatically downloaded to NAS only after completion and integrity checks.
- [PROPOSED] Operators can see independent status for local and cloud streams.
- [PROPOSED] Faculty Start/Pause/Resume/Stop controls operate on local recording only, unless explicitly specified; cloud backup is intentionally continuous.

## Non-functional requirements
- Isolation: each session uses a uniquely mapped recorder worker and storage location.
- Reliability: detect stalled/missing recording; alert and retry safely; preserve cloud fallback.
- Security: least privilege, role-based access, secure tokens, webhook signatures, audit logs.
- Privacy: clear recording notice and consent; approved retention for cloud/local archives.
- Recovery: repeatable start/join and archive reconciliation; safe after reboot or network loss.
- Maintainability: versioned markdown docs, code reviews, reproducible environments, observability.

## Non-goals at initial launch
- Replace Zoom server/media transport.
- Provide faculty host passwords.
- Circumvent Apple screen-broadcast confirmation.
- Implement unattended recorder via Meeting SDK in a way prohibited by Zoom SDK policy.
- Assume RTMS until native Windows recorder proof succeeds/fails.

## Acceptance outcomes
1. Each of four host users can independently deliver a session.
2. Both teaching modes show faculty camera + shared content + audio to remote attendees.
3. Four simultaneous local recording jobs save correct, separate final files; no cross-contamination.
4. Four cloud safety backups complete and can be downloaded.
5. Operators see channel health and archive integrity.
6. Faculty use only DocTutorials credentials and permitted invitations/SDK joins.
