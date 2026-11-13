# Milestone 2 — Secure Zoom API Smoke Test on Windows

**Updated:** 2026-11-13
**App:** DocTutorials-Backend — Server-to-Server OAuth
**State:** Test code committed; nine offline unit tests passed; **no live Zoom tenant API test has been performed**.

## Purpose

Prove that one activated DocTutorials Backend S2S OAuth app can read the four selected Zoom meeting/webinar host users without distributing their Zoom passwords to faculty.

The test authenticates with the Account ID, Client ID and Client Secret for the **same** S2S app and makes read-only Zoom API resource calls. It does not change Zoom configuration, start/stop a webinar, or control local recording.

## Prerequisites

- Trusted Windows admin workstation with Python 3.10+ and Git installed.
- The Zoom S2S app has been activated, with five granular read scopes: user:read:list_users:admin, meeting:read:list_meetings:admin, meeting:read:meeting:admin, webinar:read:list_webinars:admin, webinar:read:webinar:admin.
- The authorized admin can view App Credentials in Zoom Developer Portal. Never paste secrets or account identifiers into chat, GitHub, issue comments, or screenshots.
- Test in an interactive PowerShell window. Do not record the screen while entering credentials.

## Run the test (PowerShell)

Clone the **private** repository and run the offline tests. If you already cloned it, use git pull instead of cloning again.

    git clone https://github.com/vinodkumar-Hegde/doctutorials-zoom-suite.git
    cd doctutorials-zoom-suite
    py -3 --version
    py -3 -m unittest discover -s tests -v

You should see **nine** offline mock tests passing. This does not prove the live Zoom integration.

To run the live read-only test:

    py -3 backend\zoom_s2s_smoke_test.py

The script prompts for these three values, with your input **hidden**: Zoom Account ID; S2S Client ID; S2S Client Secret. Get all three directly from Zoom Developer Portal → DocTutorials-Backend → App Credentials. Press Enter after each. No credentials or tokens are saved to disk.

If exactly four eligible active paid/on-prem Zoom users exist, the script selects those four. If more than four exist (for example, the admin is also licensed), the script displays names only on your **own terminal** for choosing the intended four host users. Enter four different indices separated by commas. Never share a screenshot of this selection screen.

## API calls

The script uses the standard S2S account-credentials grant with **POST https://zoom.us/oauth/token**. This requests an access token, not a resource modification.

All Zoom resource requests are **GET**:
- GET https://api.zoom.us/v2/users?status=active
- GET https://api.zoom.us/v2/users/{userId}/meetings
- GET https://api.zoom.us/v2/users/{userId}/webinars
- When scheduled items exist: GET /v2/meetings/{meetingId} and GET /v2/webinars/{webinarId}.

Only unexpired scheduled meetings/webinars are returned by the list endpoints. A category with no scheduled items will have its detail check marked **SKIPPED**, not PASS. Successful list access alone does not prove missing detail permissions.

The tool reads pagination tokens, validates response structure, and on HTTP failures displays only a sanitized code and generic troubleshooting hint. It does not write tokens, user details, webinar links, API responses, or report files.

## Expected output (illustrative, not actual results)

    OAuth token request: PASS
    List active users: PASS (5 total)
    Eligible paid/on-prem host candidates: 5
    Host A: meetings=2, webinars=1, meeting detail=PASS, webinar detail=PASS
    Host B: meetings=1, webinars=0, meeting detail=PASS, webinar detail=SKIPPED (no scheduled webinar)
    Host C: meetings=0, webinars=2, meeting detail=SKIPPED (no scheduled meeting), webinar detail=PASS
    Host D: meetings=2, webinars=1, meeting detail=PASS, webinar detail=PASS
    RESULT: PASS — four separate licensed host users were read successfully. No Zoom records modified.

**Safe information to share here:** the final RESULT line, host A–D counts, and a sanitized HTTP code if the test fails. Do not send host names, emails, IDs, screenshots of the host picker, app credentials, access tokens, meeting IDs, join links, or recording content.

## Common issues

| Result | What to check |
|---|---|
| OAuth HTTP 400 / 401 | App activation; credentials must come from the same S2S app |
| Resource GET HTTP 403 | Exact read-only scopes and Zoom developer/admin role permissions; do not add write scopes |
| Resource GET HTTP 404 | Selected host user still belongs to account; check license/status |
| HTTP 429 | Rate limit; stop repeated tests and retry after a reasonable interval |
| Fewer than four candidates | Check all four host users are active and appropriately licensed |
| Zero scheduled items | Normal if no unexpired scheduled meetings/webinars exist; verify future schedules separately |
| Details SKIPPED | Detail access still requires a scheduled item to verify |

## Subsequent production steps

This is a **standalone proof-of-access**, not a production backend. Do not store the S2S credentials in source control or on faculty devices. The production FastAPI backend will use an organization-approved secret manager, short-lived in-memory token caching, narrow service accounts, redacted audit logs, and monitored failures. Zoom S2S tokens have a limited lifetime and are reacquired with the account-credentials grant; no refresh token.

Webhook event subscriptions and cloud recording download scopes are separate work items and remain deferred until the corresponding secure backend endpoint and archive functionality exist.

## Acceptance tracker

- [x] S2S app created — operator confirmed
- [x] App Information and five read-only scopes — operator confirmed
- [x] App activated — operator confirmed
- [x] Local mock-based tests — nine tests pass
- [ ] Live OAuth token request with tenant credentials
- [ ] Four intended licensed hosts selected and read
- [ ] Meetings/webinars and available individual details read
- [ ] Production secret manager provisioned
- [ ] Cloud archive API integration
- [ ] Signed HTTPS Zoom webhook receiver

Official sources:
- https://developers.zoom.us/docs/internal-apps/s2s-oauth/
- https://developers.zoom.us/docs/integrations/oauth/
- https://developers.zoom.us/docs/api/users/
- https://developers.zoom.us/docs/api/meetings/
- https://developers.zoom.us/docs/internal-apps/oauth-scopes-granular/
