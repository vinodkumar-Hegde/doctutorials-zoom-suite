# Milestone 2 — Server-to-Server OAuth Operator Runbook

**Last reviewed:** 2026-11-13  
**Status:** IN PROGRESS — operator reports `DocTutorials-Backend` created as Server-to-Server OAuth on 2026-11-13. Information and all five initial read-only scopes operator-confirmed completed on 2026-11-13; activation operator-confirmed on 2026-11-13; secure backend credential provisioning and live API verification pending.  
**Owner:** DocTutorials Zoom administrator.  
**Environment:** One Zoom organization with four licensed meeting/webinar host users.

## Purpose and boundaries

Create one **internal** Zoom Server-to-Server OAuth app named **DocTutorials-Backend**. The backend will use it to discover the four authorized Zoom host users and their scheduled meetings/webinars, then (with separately approved read permissions) find completed cloud recordings. Later it will subscribe to session and cloud-recording webhooks.

This integration does **not** sign faculty into Zoom; does **not** distribute host Zoom credentials; does **not** remotely start native Windows local recordings; and does **not** use ZAK or RTMS.

## Stage A — Account permissions (admin)

- [ ] Sign into https://marketplace.zoom.us/ as Zoom account owner/admin.
- [ ] Verify the **Developers** / **Created Apps** option is present.
- [ ] If absent, check Zoom web portal **User Management → Roles → Role Settings → Advanced features**, allowing View/Edit **Server-to-Server OAuth app** for the authorized developer. Do not broaden permissions for ordinary faculty.
- [ ] Confirm the app owner retains a role allowed to grant necessary admin scopes. Losing this role may remove app scopes.

Official: https://developers.zoom.us/docs/internal-apps/ and https://developers.zoom.us/docs/internal-apps/create/

## Stage B — Create the app (admin)

- [x] Developer → Created Apps → **+** → **Build an app** (operator-confirmed).
- [x] Select **Server-to-Server OAuth**; click **Create** (operator-confirmed).
- [x] Name it **DocTutorials-Backend** (operator-confirmed).
- [ ] On **App Credentials**, identify **Account ID**, **Client ID**, **Client Secret**. Place them only in an approved secret manager under keys named below. Never paste values into chat, screenshots, GitHub, tickets, logs, or spreadsheets. Do **not** share credentials with faculty.
- [x] Complete **Information** (operator-confirmed, individual fields not independently inspected): short description `Internal integration for managing DocTutorials Zoom meetings, webinars, faculty sessions, and recording backups.`; company `DocTutorials` (use the verified legal/company name if required); authorized developer contact name and email (required for activation). No exact personal contact details are committed.

**No redirect URI is required for the Server-to-Server OAuth account-credentials grant**. It does not require an interactive end-user consent login.

## Stage C — Read-only scopes (minimum initial proof)

**Operator reported all five initial read-only scopes saved on 2026-11-13; not independently inspected in Zoom.**

In **Scopes → Add Scopes**, search for and select these specific **admin** granular permissions. Add only those actually required for the first test. All names below are documented in Zoom's granular scope table:

| Exact granular scope | Purpose |
|---|---|
| `user:read:list_users:admin` | Read organization users; identify approved four host aliases |
| `meeting:read:list_meetings:admin` | List each user's meetings |
| `meeting:read:meeting:admin` | Get a specific meeting's metadata |
| `webinar:read:list_webinars:admin` | List each user's webinars |
| `webinar:read:webinar:admin` | Get a specific webinar's metadata |

**Cloud archive addition, when implementing download**:

| Exact granular scope | Purpose |
|---|---|
| `cloud_recording:read:list_account_recordings:admin` | Find recorded sessions in the account |
| `cloud_recording:read:list_recording_files:admin` | Find files and download URLs for a recording |

Cloud recording scopes grant access to potentially sensitive recordings. Add them at the archival integration test (or now if the organization expressly authorizes the test); store any retrieved content in protected storage. No recording delete/update, meeting/webinar create/update or ZAK scopes in this first configuration.

Scopes verified against https://developers.zoom.us/docs/internal-apps/oauth-scopes-granular/ and https://developers.zoom.us/docs/api/meetings/.

## Stage D — Features / Webhooks (defer until endpoint deployed)

**2026-11-14 screenshot review:** The app's Feature page shows Event Subscriptions **OFF**, as intended. The screenshot also displayed the **Webhook Secret Token** in readable text. **Action required before any webhook use:** regenerate only this Webhook Secret Token via **Feature → Token → Regenerate**, keep Event Subscriptions OFF, and do not publish/display the replacement token. Rotation is **not yet operator-confirmed**. This token is distinct from S2S App Credentials/Client Secret; regenerating the webhook token does not change meeting/webinar configuration. Review any existing webhook consumer before rotating, though none is configured for this new app based on the visible toggle.

- [ ] Operator confirms rotation of screenshot-exposed **Webhook Secret Token**; never log the old or new token.


- [ ] Do not enable/activate event subscriptions against an invented URL or third-party webhook receiver.
- [ ] First deploy a **public HTTPS TLS 1.2+ fully qualified domain** endpoint handling POST and Zoom's `endpoint.url_validation` challenge-response within three seconds.
- [ ] Verify HMAC SHA256 signatures using `x-zm-request-timestamp`, the **raw** request body, and the Zoom webhook secret; check timestamp skew, dedupe events, and avoid secret/token logging.
- [ ] Then enable **Event Subscriptions** in **Features → Access** (or the equivalent current app Features screen). Set receiver to **All users in your account** when using Marketplace UI, to observe the four host users.
- [ ] Subscribe first to `meeting.started`, `meeting.ended`, `webinar.started`, `webinar.ended`, and `recording.completed`, subject to the app UI showing those exact events and required scopes.
- [ ] Click **Validate** for the endpoint, then **Save** and run test events.
- [ ] Never interpret `recording.completed` as a Windows **local recording** event. It is for completed Zoom **cloud** recordings.

Official: https://developers.zoom.us/docs/api/webhooks/ and https://developers.zoom.us/docs/api/meetings/events/

## Stage E — Activate and prove API access (after scopes)

- [ ] Resolve app's Information/Scopes/Activation validation warnings.
- [x] Activate the **internal** app (operator-confirmed 2026-11-13; token-based confirmation still pending).
- [ ] Store `ZOOM_ACCOUNT_ID`, `ZOOM_S2S_CLIENT_ID`, `ZOOM_S2S_CLIENT_SECRET` in an approved server-side vault. They must not appear in frontend/iPad/Windows builds or git.
- [ ] The backend obtains a time-limited token using POST `https://zoom.us/oauth/token`, grant `account_credentials`, account_id, and HTTP Basic client credentials. No refresh token: reacquire on expiry, securely cache per service.
- [ ] Verify `GET https://api.zoom.us/v2/users`, then for each approved host: `GET /users/{userId}/meetings` and `GET /users/{userId}/webinars` (use the exact Zoom API syntax per endpoint). Do not put raw user IDs in public logs.
- [ ] Confirm list/get access respects existing live sessions and makes **no write requests**. Capture non-sensitive test evidence: HTTP status; number of approved hosts matched; pagination count; scope errors if any. Never paste access token or response bodies containing faculty/student information.
- [ ] Enable authorized cloud recording list/download test later; verify MP4 checksum and secure storage without deletion.

Official: https://developers.zoom.us/docs/internal-apps/s2s-oauth/

## Acceptance evidence (currently pending)

| Proof | Status |
|---|---|
| App creation under correct Zoom organization | OPERATOR REPORT: CREATED; organization ownership not independently checked |
| App activation | OPERATOR REPORT: ACTIVATED; token exchange pending |
| Exact permitted read-only scopes | OPERATOR REPORT: ALL FIVE SELECTED; activation/API verification pending |
| Secure server-side secret storage | NOT YET VERIFIED |
| API read of four approved host users | NOT YET VERIFIED |
| Read of host meeting and webinar schedules | NOT YET VERIFIED |
| Cloud recording list/download | NOT YET VERIFIED |
| HTTPS webhook CRC, signature and event tests | NOT YET VERIFIED |

## Operator handoff, first screen

**App created, Information and five scopes configured (operator-confirmed).** **S2S app created, information and five initial scopes configured, and activation completed (operator-confirmed).** Next: run the standalone secure API smoke test from an authorized Windows admin workstation using local hidden credential prompts. Do not share Account ID, Client ID, Client Secret, access token, host IDs or credential-bearing screenshots. A separate production vault and backend integration remain pending; webhook features are deferred.

## Rollback

This stage does **not** require changing existing webinar or cloud recording settings. If activation fails, stop and note the displayed non-sensitive error; do not widen scopes or alter live meeting settings blindly. Deactivating or removing an app later must be scheduled because that interrupts the backend integration once in service.

## Stage F — Live read-only API test (ready for operator)

The standalone Windows test implementation and precise private-input instructions have been published in [16-MILESTONE-2-SECURE-API-SMOKE.md](16-MILESTONE-2-SECURE-API-SMOKE.md). The repository now contains the Python 3 standard-library-only implementation in [../backend/zoom_s2s_smoke_test.py](../backend/zoom_s2s_smoke_test.py) and its nine mock-based tests in [../tests/test_zoom_s2s_smoke_test.py](../tests/test_zoom_s2s_smoke_test.py).

**Status:** Script published; offline unit tests passed; actual Zoom token exchange and four-host GETs **NOT YET RUN**. Operator to execute on trusted Windows workstation, sharing only redacted Host A–D count/results. Vault and HTTPS webhooks remain pending.
