# Zoom Developer Apps Configuration — Stage 2 in progress

**Admin-only setup. Do not store real secrets in this repository.** Current Server-to-Server OAuth steps and relevant read-only granular scopes were checked against Zoom official documentation on 2026-11-13. Operator confirms `DocTutorials-Backend` S2S app created on 2026-11-13; Information and five read-only admin scopes operator-confirmed complete; activation operator-confirmed; secure backend credentials, API responses, and entitlement are not yet independently verified.

## App A: `DocTutorials-Backend` — Server-to-Server OAuth
Purpose: manage meeting/webinar schedules for the four users, read metadata, and archive completed **cloud** recordings. This app uses Zoom account-level backend authorization.

1. Zoom App Marketplace → Develop → Build App → **Server-to-Server OAuth**.
2. Record account ID, app client ID and client secret in a secure secret manager, **never** in markdown, GitHub issues, or chat.
3. Set least-privilege scopes for host-user discovery, meeting/webinar metadata, and cloud recording retrieval. Add create/update scopes only if scheduling is implemented.
4. Enable event subscriptions only after secure public HTTPS webhook URL exists.
5. Validate Zoom endpoint URL challenge and all signed events. Deduplicate by event ID/meeting UUID/time, handle retries.
6. Subscribe only to necessary current event names, e.g. `meeting.started`, `meeting.ended`, `webinar.started`, `webinar.ended`, `recording.completed`; verify that relevant event names are present in the current app.
7. Test queries for all four host users. Redact identifiers in logs/docs.

Important: Server-to-Server OAuth does **not** provide local-recording control and **does not** issue a Zoom login to faculty.

## App B: `DocTutorials-iPad` — General App + Meeting SDK
Purpose: render an interactive faculty Zoom webinar experience in branded iPad app.

1. Zoom App Marketplace → General App → Meeting SDK embedding feature.
2. Create **backend-generated, short-lived** SDK authentication signatures or tokens per official iOS SDK requirements. Keep SDK secrets off the device.
3. Implement Zoom webinar panelist entitlement and join flow; test panelist vs attendee permissions and any authentication requirements before productizing.
4. Develop SwiftUI app with ReplayKit Broadcast Upload Extension and `MobileRTCScreenShare.framework`, consistent with the SDK version.
5. iPad user must manually confirm Start Broadcast using Apple system UI.
6. Evaluate Zoom Marketplace app-review requirements, Apple TestFlight, then deployment method.

Official: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/ and https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/screen-share/

## App C: `DocTutorials-Windows` — General App + Plugin SDK
Purpose: communicate with each installed Zoom Workplace Windows client and control **supported** actions. This is not an unattended Meeting SDK bot.

1. Zoom App Marketplace → General App → Features → Access → Plugin SDK → Windows.
2. Zoom Workplace **7.0.2+**; compatible Windows SDK and Visual Studio 2019+ (verify current SDK matrix).
3. Use the documented OAuth `plugin_sdk:read:connection_meta` permission to authenticate the Plugin SDK connection; add other scopes only as required and supported.
4. Verify client user identity and meeting ID; audit local recording start, stop, pause, resume, and callback support in a single-host proof of concept.
5. Test four concurrent channels with isolated authorized Zoom client instances. Use physical-worker fallback if VMs fail.

Official: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/ and https://developers.zoom.us/docs/plugin-sdk/windows/integrate/

## Not selected for MVP
- **ZAK**: not needed merely for Server-to-Server OAuth and ordinary faculty webinar panelist joining. Revisit only if an authenticated Meeting SDK host flow explicitly requires it.
- **RTMS**: fallback for acquiring real-time streams, but introduces media processing and licensing/credit implications.
- **Meeting SDK for unattended recorder bots**: not supported as a generic bot architecture per current Zoom SDK policy.

## Environment variable names
See `.env.example`; values live only in secret manager. No credentials or tokens in git.

## Milestone 2 operator walkthrough (2026-11-13)
The step-by-step, scope-exact runbook is in [`15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md`](15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md). The operator has created **DocTutorials-Backend** as a Server-to-Server OAuth app. The operator reports Information and five read-only admin scopes configured. Activation is now operator-confirmed. Next: run the safe read-only API smoke test using local hidden credential prompts; do not store credentials in source or chat, and do not enable webhooks yet. Webhooks remain deferred. Add admin read scopes for four-host user, meeting and webinar metadata; defer the HTTPS webhook subscription until the endpoint is deployed. Do not mistake activation or written docs for an actual tested app.
