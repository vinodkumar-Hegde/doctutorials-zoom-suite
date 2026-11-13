# Milestone 2 — Secure Zoom API Smoke Test on Windows

**Updated:** 2026-11-14
**App:** DocTutorials-Backend — Server-to-Server OAuth
**State:** Operator Windows **13/13 offline tests PASS**. One-user Basic sandbox live S2S OAuth token exchange, active users GET (1), and meetings-list GET (0) **PASS** on 2026-11-14. Meeting detail GET skipped (none scheduled); webinar and four-host production verification **PENDING**.

## Purpose

Prove that one activated DocTutorials Backend S2S OAuth app can read the four selected Zoom meeting/webinar host users without distributing their Zoom passwords to faculty.

The test authenticates with the Account ID, Client ID and Client Secret for the **same** S2S app and makes read-only Zoom API resource calls. It does not change Zoom configuration, start/stop a webinar, or control local recording.

## Prerequisites

- Trusted Windows admin workstation with Python 3.10+ and Git installed.
- The Zoom S2S app has been activated, with five granular read scopes: user:read:list_users:admin, meeting:read:list_meetings:admin, meeting:read:meeting:admin, webinar:read:list_webinars:admin, webinar:read:webinar:admin.
- The authorized admin can view App Credentials in Zoom Developer Portal. Never paste secrets or account identifiers into chat, GitHub, issue comments, or screenshots.
- Test in an interactive PowerShell window. Do not record the screen while entering credentials.

## Operator workstation verification (2026-11-14)

The operator confirmed Python 3.11.9 and Git 2.56.0 on Windows, successfully cloned the private repository and ran **all nine** offline tests with `python -m unittest discover -s tests -v` (`OK`). Git was made available in the current PowerShell session by adding `C:\Program Files\Git\cmd` to `$env:Path`; this adjustment is not persistent across new shells. The script can be launched using `python` without the optional `py` launcher.

## Run the test (PowerShell)

Clone the **private** repository and run the offline tests. If you already cloned it, use git pull instead of cloning again.

    git clone https://github.com/vinodkumar-Hegde/doctutorials-zoom-suite.git
    cd doctutorials-zoom-suite
    py -3 --version
    py -3 -m unittest discover -s tests -v

You should see **13** offline mock tests passing. Offline tests alone do not prove the live Zoom integration.

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

## Safety with existing sessions and integrations

The smoke test uses a Zoom OAuth **token exchange** and **GET** resource endpoints only. It has no capability to create, edit, delete, start, or end meetings/webinars; it does not modify Zoom cloud-recording settings, existing Developer Apps, app subscriptions or active sessions. It does not need to be run during a live class.

**Limited operational caveat:** Zoom API quotas are account-wide and shared across all applications installed on that account. This one-off test makes a small number of requests, but on an already rate-limited account it could contribute to HTTP 429 responses for existing integrations. Run it **once during a quiet/off-peak window**, avoid parallel repeated tests, and stop on any error. For maximum isolation, do the first validation against a nonproduction Zoom account if one with representative licenses is available, or run the production-account smoke test outside active classes. The read-only test does not guarantee that an existing integration will never experience rate limiting.

Official: https://developers.zoom.us/docs/api/rate-limits/

## One-user sandbox test (separate from production acceptance)

On 2026-11-14, the operator's S2S app credentials successfully authenticated and listed one active Zoom user, but **zero eligible licensed hosts**. The operator subsequently confirmed these credentials were from their **free Zoom Basic sandbox**, not the four-host production organization. The default command deliberately rejected the four-host acceptance test rather than falsely passing.

The script now supports an **explicit opt-in** one-user read-only sandbox mode. Run on a trusted Windows workstation **from the cloned repository directory**:

    git pull
    python -m unittest discover -s tests -v
    python backend\zoom_s2s_smoke_test.py --sandbox-single-user

This mode:
- Requires **exactly one active Zoom user** with a valid ID; rejects any multi-user organization in sandbox mode.
- Accepts a Basic user and tests OAuth, users, the user's scheduled-meetings list, and a meeting-detail GET when a scheduled meeting exists.
- **Does not call webinar APIs**, cloud recordings, or change meetings.
- Labels results as **SINGLE-USER SANDBOX**, never as four-host production acceptance.
- Keeps the default `python backend\zoom_s2s_smoke_test.py` behavior unchanged and requires four eligible paid hosts there.
- Uses the same three hidden prompts. Credentials must come from the app belonging to the tenant intended for this run; never share them with chat or commit them.

**Operator validation (2026-11-14):** All **13** offline tests passed. The live one-user Basic sandbox run reported OAuth PASS, list active users PASS (1), sandbox meetings list GET succeeded (0), and overall RESULT PASS. Meeting-detail GET was SKIPPED for lack of a scheduled future meeting; webinar not tested. Four-host production acceptance is still pending.

If the one-user result was unexpected and the operator intended to reach an organization with four licensed hosts, **do not switch on sandbox mode to mask the issue**. Instead check the Zoom signed-in organization and the Account ID, Client ID and Client Secret associated with the intended activated S2S app. Do not mix credentials from two apps or paste them into chat.

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
- [x] Live OAuth token request with **sandbox** tenant credentials (no secrets shared)
- [x] Basic sandbox active user GET and scheduled meetings list GET; zero future meetings, detail GET skipped
- [ ] Sandbox meeting detail GET after scheduling a throwaway future test meeting
- [ ] Four intended licensed production hosts selected and read
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

## 2026-11-14 — Repeated zero-meeting sandbox results and operator next action

The operator reran the single-user sandbox test twice: OAuth PASS, active users GET PASS (1), meetings-list GET PASS (0), and detail SKIPPED both times. This is **not** an API authentication or permissions failure. Per [Zoom's List Meetings API](https://developers.zoom.us/docs/api/meetings/), `GET /users/{userId}/meetings` defaults to `type=scheduled` and returns a host's unexpired scheduled meetings, not instant meetings. The script's existing query uses that default. No API code change is needed.

**Operator action:** In the same free Zoom account associated with the sandbox app's credentials, schedule and **save** one ordinary future meeting (not instant, PMI-only or an invite to someone else's meeting), confirm it appears in the account's scheduled-meetings list, and rerun `python backend\zoom_s2s_smoke_test.py --sandbox-single-user`. Expected: `meetings>=1` and `meeting detail=PASS`. If the Zoom UI lists a future meeting but the API still shows zero, investigate account identity, meeting host and filter without sharing meeting details or account IDs. Production four-host test remains pending.
