# Gate 2B — Local Meetings Backend (Free Zoom Sandbox)

**Date:** 2026-11-14
**Implementation:** Initial sandbox-only FastAPI service committed. **Not yet run on operator's PC**. Operator's last confirmed checks are 15/15 unit tests and standalone read-only Zoom sandbox test (one meeting, detail PASS).

## Scope and safety

This is a **local development proof**, not a production backend. Its only Zoom operations are a short-lived server-side token grant, `GET /users`, `GET /users/{userId}/meetings` and `GET /meetings/{meetingId}`.

Safeguards:
- The service deliberately requires **exactly one active Basic Zoom user** (`type=1`). It refuses multi-user and paid production organizations.
- FastAPI listener is bound to **127.0.0.1** only. Do not forward port 8765, modify host binding, run it as a public service, or expose it to the internet.
- A randomly generated **session-only local API key** must accompany all API requests in `X-DocTutorials-Key`; no open documentation UI. This is only a development boundary, not a production identity/RBAC design.
- App Credentials are entered with hidden prompts in the **server** process or sourced from its private environment; never entered in the browser or copied to chat.
- Responses include only a local ordinal reference, topic, start time, duration, timezone and status where available; do not return raw meeting IDs, email, join URL, passwords, account IDs or Zoom access tokens.
- The server uses in-memory OAuth token reuse and conservatively reacquires after 20 minutes. It does not persist credentials or Zoom tokens.
- All webinar APIs, webinar event subscriptions, recording actions and write scopes are deferred.
- Do not run against the production Zoom organization. Use the separate free Zoom Basic sandbox app's own credentials.

## Install once on the Windows workstation

Open PowerShell. From any directory, enter:

    cd "$HOME\doctutorials-zoom-suite"
    git pull
    python -m unittest discover -s tests -v
    python -m pip install -r backend\requirements-local.txt

The previous 15 tests passed; the new service adds **8** standard-library unit tests, so the current suite now contains **23** tests. **They have not yet been confirmed passing on the operator Windows PC.** Stop and report any failure before running the local HTTP server.

If `python -m pip` reports a missing pip installation, fix it with official Python installation instructions rather than installing random packages from unknown websites.

## Start the local backend (PowerShell window A)

Run:

    cd "$HOME\doctutorials-zoom-suite"
    python -m backend.meetings_api

Enter the three **free Zoom sandbox S2S credentials** at hidden prompts. These must NOT be the four-host production credentials.

If the sandbox Basic-account guard passes, the server displays:

    Local API listening only on http://127.0.0.1:8765
    Session-only X-DocTutorials-Key (keep private; enter when prompted by local client):
    [LOCAL SECRET KEY]

**Do not paste the local key in chat, take a screenshot of the displayed key, or put it in a command-line argument.** Keep window A open while testing. The key is randomly regenerated on each launch and is not saved.

If the program refuses to start because there are not exactly one active Basic user, **do not bypass the guard**. Verify the sandbox app/account credentials locally.

## Test authenticated endpoints (PowerShell window B)

Open a **second** PowerShell window and run:

    cd "$HOME\doctutorials-zoom-suite"
    python -m backend.meetings_api_client

Paste the temporary API key displayed in window A into the hidden prompt.

The client calls:
1. `GET http://127.0.0.1:8765/v1/meetings` with the local API key.
2. If the list is nonempty, `GET http://127.0.0.1:8765/v1/meetings/1` with the same key.

Expected format, if the previously verified future sandbox meeting is still scheduled:

    Local authenticated meetings GET: PASS, count=1
    Local authenticated first meeting detail GET: PASS
    RESULT: PASS — Local Zoom Basic Meetings service. No webinar APIs.

This is **illustrative**; another count is possible if the sandbox meeting has expired or additional future meetings were scheduled.

## Stop server and report

Press **Ctrl+C** in window A. Do not configure Windows startup tasks or open firewalls to automate the service.

Share only the 23-unit-test summary and the client `RESULT` lines. Do not share API keys, Zoom credentials, IDs, meeting topics, join URLs, terminal screenshots showing secrets, or raw JSON responses.

## What this does NOT prove

- Production deployment or adequate service authentication/RBAC.
- Persistent encrypted secret-vault configuration.
- Automatic meeting creation, editing, deletion or start/stop.
- Zoom webhook signing and lifecycle updates.
- Windows local recording, multi-channel isolation or cloud backup.
- Webinar/Meeting SDK functionality or four licensed hosts.

Those capabilities remain separate acceptance gates.

## Files

- `backend/meetings_service.py` — sandbox-only read model, in-memory token renewal and response field allowlist.
- `backend/meetings_api.py` — localhost FastAPI authenticated GET routes and fail-closed startup.
- `backend/meetings_api_client.py` — local hidden-key smoke client.
- `backend/requirements-local.txt` — development dependencies.
- `tests/test_meetings_service.py` — 8 pure-Python unit tests.

## Official sources

- Zoom Meetings API: https://developers.zoom.us/docs/api/meetings/
- Zoom S2S OAuth: https://developers.zoom.us/docs/integrations/oauth/
- FastAPI API-key header: https://fastapi.tiangolo.com/reference/security/
