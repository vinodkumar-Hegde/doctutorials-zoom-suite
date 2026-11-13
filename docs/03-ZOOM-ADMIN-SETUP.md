# Zoom Admin Setup — Cloud Backup First

**Goal:** ensure every eligible scheduled meeting/webinar of the four host users receives a Zoom cloud safety recording automatically, before building local capture.

**Current state (2026-11-13):** The operator reports this milestone already implemented. Treat the numbered configuration instructions below as a reference/runbook, **not a request to change live settings again**. Collect evidence for the acceptance items; then focus on Developer App setup.

## Instructions for account admin
1. Log in to the **Zoom Web Portal** (not Developer Console). Navigate to **Admin Center → Settings → Recording & Transcript** (older interfaces: Account Management → Account Settings).
2. Enable **Cloud recording** and select suitable video/share recording layouts. Keep recording permissions/notifications in accordance with organizational consent policies.
3. Enable **Automatic recording → Record in the cloud**. Consider locking it at the account or group level for all four hosts after verifying no other host users are unintentionally affected.
4. Audit **existing scheduled meetings, recurring sessions, and webinars individually**: changing the account default generally does not retrofit them.
5. Test a sample **meeting** and a sample **webinar** for each class of host license. Note: automatic cloud/local recording does **not** start in webinar practice sessions.
6. Verify account cloud recording storage, licensing, retention and available quota; do not assume a specific included GB allocation until admin confirms their current subscription.
7. Record test results in `docs/ZOOM-CONFIG-CHECKLIST.md`; do not paste real account IDs, personal invitation links, passwords or screenshots containing secrets into git.
8. Keep local-recording permission enabled where required for Windows workers, but treat it as a separate recording mechanism.

## Backup retention & recovery
- Proposed: cloud backup remains available until NAS has independently verified a downloadable copy and the organization's retention policy allows deletion.
- Never configure automatic destructive cloud cleanup at the first milestone.
- Configure access control, consent notices and deletion policy before broad use.
- Cloud `recording.completed` means downloadable media available; **it does not mean the Windows local recording exists**.

## Acceptance test (1 host, then 4)
- [ ] New meeting is automatically recorded in cloud.
- [ ] New webinar is automatically recorded in cloud when live (not merely practice).
- [ ] Previously scheduled webinar has been checked/updated.
- [ ] Cloud playback includes expected audio, share and speaker video.
- [ ] Recording appears under correct host account and is downloadable.
- [ ] Storage quota, retention, and sharing privileges verified.

Official docs: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0067954 and https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0058972
