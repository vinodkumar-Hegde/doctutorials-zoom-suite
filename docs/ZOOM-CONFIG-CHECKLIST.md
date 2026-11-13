# Zoom Configuration Checklist — Start Here

Do not put account credentials, account IDs, webinar passcodes, signed join URLs, SDK secrets, bearer tokens or sensitive screenshots in this document.

**Operator update (2026-11-13):** Milestone 1 automatic cloud recording configuration has already been implemented. This checklist intentionally leaves individual evidence checks open until redacted screenshots, test recording identifiers, or acceptance results are supplied. Do not interpret unchecked boxes as instructions to redo the live settings.

## A. Account overview
- [ ] Admin login available to authorized operator.
- [ ] Four **licensed host users** confirmed (use aliases e.g. Host A/B/C/D, not emails).
- [ ] Host A webinar/meeting entitlement and capacity confirmed.
- [ ] Host B webinar/meeting entitlement and capacity confirmed.
- [ ] Host C webinar/meeting entitlement and capacity confirmed.
- [ ] Host D webinar/meeting entitlement and capacity confirmed.
- [ ] Identify any other account users that may be affected by locked account-wide recording defaults.

## B. Automatic cloud recording — all four hosts
**Configuration:** Reported implemented for four accounts; **functional verification:** pending.
- [ ] Go to Admin Center → Settings → Recording & Transcript.
- [ ] Cloud recording enabled.
- [ ] Automatic recording enabled → **Record in the cloud**.
- [ ] Lock/account-group policy selected intentionally, after checking impacted users.
- [ ] Recording notification/privacy policy reviewed.
- [ ] Cloud layout settings reviewed (speaker + screen share as desired).
- [ ] Verify default applies to NEWly scheduled meetings/webinars.
- [ ] Audit and update EXISTING meetings/webinars/recurring sessions.
- [ ] Confirm practice sessions don't trigger automatic webinar cloud recording.
- [ ] Test an actual live meeting on Host A.
- [ ] Test an actual live webinar on Host A.
- [ ] Repeat cloud safety check on Hosts B/C/D.
- [ ] Confirm cloud recordings appear and can be downloaded.
- [ ] Verify quota, backup retention, deletion rights, and operator access.

## C. Preparations for developer apps (later)
- [ ] Admin Zoom Marketplace Developer access available.
- [ ] Secure HTTPS domain for callbacks planned.
- [ ] Secret manager prepared.
- [ ] Zoom S2S OAuth app created with least-privilege scopes.
- [ ] Zoom webhooks validated and signed.
- [ ] Windows Plugin SDK app created and single-channel test passes.
- [ ] iPad Meeting SDK app created and webinar panelist share test passes.

## D. Local recording and faculty (later)
- [ ] Native Windows Zoom recorder test: correct host/user permission.
- [ ] Local recorder successfully captures laptop-only class.
- [ ] Local recorder successfully captures laptop+iPad shared screen class.
- [ ] Four-channel concurrent recording passed.
- [ ] NAS archive verifies MP4/checksum before deleting nothing prematurely.

## Notes
Date/configured by: Operator confirms implemented on 2026-11-13; exact prior configuration date not supplied. Record redacted observations only; use secure internal inventory for identifying account data.
