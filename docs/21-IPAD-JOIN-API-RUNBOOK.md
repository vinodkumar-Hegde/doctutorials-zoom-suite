# Stage 4B — iPad Sandbox Meeting Join API (staged; not deployed)

**Scope:** One non-host participant using the **DocTutorials-iPad Meeting SDK General App** and a meeting owned by the **separate Zoom Basic sandbox**. Faculty laptop handles audio/video, the iPad is a second participant. No webinars, production Zoom host credentials, or Windows recording changes.

## Implementation in repository (2026-11-15)

| Module | Purpose | Status |
|---|---|---|
| backend/ipad_sdk_jwt.py | Backend-only Meeting SDK HS256 JWT, participant role=0 | 8/8 offline tests verified on operator Mac |
| backend/ipad_join_authorization.py | Server-owned faculty-to-session assignment + eligible time window | 12/12 offline tests verified on operator Mac |
| backend/ipad_join_http.py | POST /api/sessions/{session_id}/join/ipad | **Committed, disabled by default; HTTP tests unverified** |
| tests/test_ipad_join_http.py | 19 offline HTTP contract/security test methods | Committed; **not yet run** |
| backend/requirements-ipad-dev.txt | FastAPI, Uvicorn + httpx TestClient dependencies | Committed; not installed on Mac |
| ipad/DocTutorialsScreenShare/SDKApp/HTTPSFacultyJoinTicketClient.swift | HTTPS-only URLSession ticket client, in-memory token, explicit errors | Committed, **not yet compiled** |
| ipad/DocTutorialsScreenShare/SDKApp/ZoomMeetingJoinAdapter.swift | SDK init, backend JWT authorization, non-host meeting join, observed callback state | Compiled in earlier SDK-enabled build but **not connected to UI** |

**This is an interface and authorization boundary, not a working faculty login or a deployed live API.** There is intentionally **no executable main, development login bypass, sample bearer token endpoint, unauthenticated test API or production credentials**.

## HTTP contract

A trusted DocTutorials backend will, only after faculty authentication:

- Accept HTTPS **POST** to /api/sessions/{internal_session_id}/join/ipad with **Authorization: Bearer {verified faculty access token}** and **no request body**.
- Require an explicit backend enable switch and a concrete trusted hostname. Deny all plaintext HTTP requests. Deploy with correct TLS termination and trusted-proxy ASGI scheme; do not blindly trust client-supplied X-Forwarded-Proto.
- Delegate bearer verification to a configured **real faculty identity verifier**. It must verify token cryptographic signature, issuer, audience, expiry/clock skew, and current faculty activation/revocation state, using the DocTutorials identity service. Untrusted JWT decoding alone is NOT authentication; Zoom Meeting SDK JWT is NOT a faculty access token.
- Look up the requested assignment from a **server-owned repository**, not an iPad payload or query parameter: correct faculty ID; correct internal session; environment=zoom_basic_sandbox; join_enabled; numeric meeting ID; meeting start -15 minutes through end +15 minutes.
- Sign a backend-only 30-minute Meeting SDK JWT with the **separate DocTutorials-iPad General App's Meeting SDK Client ID/Secret** from a backend secret manager. No S2S OAuth secret, no Zoom host credentials, no production Zoom details.
- On 200, return only this ephemeral response (exact key names, all values placeholders):

```json
{
  "meetingNumber": "12345678901",
  "meetingPasscode": "<server-managed sandbox meeting passcode>",
  "displayName": "Authorized Faculty",
  "meetingSDKJWT": "<sensitive short-lived SDK JWT>",
  "expiresAtEpoch": 1800001800
}
```

- Return generic **401** for absent/invalid faculty token; **403** for unknown/unauthorized meeting; **400** for any body; **426** for plaintext HTTP; **503** when feature disabled. Every response is marked Cache-Control: no-store, private. OpenAPI docs disabled. No CORS allowance. Do not log a ticket, raw Authorization header or Zoom credentials.
- Apply ingress-level **rate limits, request-size limits, TLS, WAF as needed, and verified auth session policies** before enabling. Ensure any reverse-proxy request logging never includes credentials.
- A successful HTTP ticket is not evidence of a Zoom Meeting join. The iPad must receive a real Zoom SDK .inMeeting callback. ReplayKit broadcast requires separate entitlement, privacy toggle, extension, and Apple OS confirmation.

**Do not expose backend/meetings_api.py to faculty.** That loopback-only local GET proof is an operator test tool with a different security principal and serves no join tickets.

## Mac offline tests — no secrets or Zoom calls

From Mac Terminal:

```bash
cd ~/doctutorials-zoom-suite
git pull
python3 -m venv "$HOME/.venvs/doctutorials-ipad-api"
"$HOME/.venvs/doctutorials-ipad-api/bin/python" -m pip install -r backend/requirements-ipad-dev.txt
"$HOME/.venvs/doctutorials-ipad-api/bin/python" -m unittest discover -s tests -p 'test_ipad_join_http.py' -v
```

Expected **19 tests / OK** if all succeed; **NOT YET VERIFIED on Mac or by a live server**. They use FastAPI TestClient with fake faculty verifier and fake meeting assignment. No Zoom credentials or public server.

To compile the newly committed Swift ticket client as part of the SDK-enabled app:

```bash
cd ~/doctutorials-zoom-suite/ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
```

Choose iPad (A16) and press Cmd+B, then Cmd+U. **Compilation and five existing tests against the newly added Swift source are still pending operator confirmation.** Do NOT enable Join on a sample lecture. The client accepts only HTTPS base URL and a validated faculty token, with an ephemeral URLSession and no plaintext file storage.

## Missing prerequisites before real sandbox join

1. Select and integrate the actual **DocTutorials faculty sign-in / identity provider** (currently unspecified). Verify issuer, audience, asymmetric signature, expiry and active faculty state against a trusted user registry. No demo-token bypass.
2. Implement the server-owned **faculty-to-sandbox-meeting assignment repository** with authorization, schedule checks, and secure passcode retrieval. No assignment sourced from iPad inputs.
3. Configure backend secret manager with the sandbox Meeting SDK General App **Client ID/Secret**, protect and rotate it. Never share secret text via chat, screenshots or GitHub.
4. Deploy or test a **proper authenticated HTTPS backend** with trusted TLS reverse proxy and rate limiting; the disabled app-factory code is not a server deployment.
5. Integrate the iPad **faculty login + assigned session list** and feed the validated access token to HTTPSFacultyJoinTicketClient. Then and only then enable Join and invoke ZoomMeetingJoinAdapter.
6. Independently verify observed **.inMeeting** SDK callback, muted microphone/video, Zoom meeting security prompts, stop/leave/rejoin. On a real iPad, later implement App Group + ReplayKit Broadcast Upload Extension and share permission callbacks.

## Relevant sources

- Zoom Meeting SDK JWT authorization and internal-account participant rules: https://developers.zoom.us/docs/meeting-sdk/auth/
- Zoom iOS joining and meeting-state callbacks: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- FastAPI deployment and HTTPS deployment guidance: https://fastapi.tiangolo.com/deployment/https/
- Starlette TrustedHostMiddleware: https://www.starlette.io/middleware/
- Apple ATS HTTPS network guidelines: https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity
