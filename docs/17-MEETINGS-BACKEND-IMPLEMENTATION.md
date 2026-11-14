# Gate 2B — Meetings-Only Secure Backend Implementation

**Date:** 2026-11-14
**Decision:** ADR-014 — Implement and accept Zoom Meetings integration before starting webinar integration.
**Scope status:** Increment A local prototype **operator-tested (authenticated list/detail GET PASS)** on 2026-11-14. Operator reports all 23 offline tests PASS; full acceptance remains pending on explicit negative-authentication validation and security review. Not a production deployment.

## Evidence establishing readiness

The operator ran the current smoke test on a Windows workstation using the separate free Zoom Basic sandbox:

- **15/15** standard-library offline Python unit tests PASS.
- S2S OAuth token exchange PASS.
- `GET /users` PASS (one active sandbox user).
- `GET /users/{userId}/meetings` PASS (one future meeting).
- `GET /meetings/{meetingId}` PASS for the sandbox scheduled meeting.
- No webinar endpoints invoked; no production four-host results available.
- No credentials were shared and no Zoom resource writes were made.

These results close the initial **sandbox meetings read-only API proof**. The production backend, recording workflows, create/update APIs and four-host verification remain **pending**.

## Proposed implementation increments

### Increment A — Local read-only service (initial code committed; acceptance pending)

Build a FastAPI service consuming Zoom Server-to-Server OAuth credentials **only on the server**. For the first local demonstration:
- Bind to **127.0.0.1 only** (never expose to LAN/public internet).
- Use the free Basic sandbox app credentials entered privately into the local operator process or an approved secret provider, not in Python source, command-line flags, browser code or GitHub.
- Validate **one active Basic sandbox user** before accessing meetings; fail closed on unexpected users/accounts. Production multi-host mappings require separate provisioning and approval.
- Cache the Zoom bearer token in memory with bounded expiry; reauthenticate safely on expiry; no client-side Zoom secrets.
- Expose **GET-only** local meeting list and meeting detail endpoints, behind an explicit operator authentication check; return allowlisted fields and omit join links, passwords, access tokens, email and host IDs.
- Disable verbose debug traces, unnecessary OpenAPI exposure and request/response body logs. Add timeouts, sanitized errors, and input validation.
- Do **not** enable Zoom Event Subscriptions or any write scope.

### Increment B — Meeting lifecycle proof

After read-only backend approval, investigate whether read-only meeting state can be polled or verified through authenticated official meeting APIs. Implement Zoom meeting webhooks only after a public HTTPS endpoint supports signed verification, replay protection, event idempotency and subscription challenge. Keep webhooks separate from recorder status and from the cloud safety backup.

### Increment C — Authorized meeting changes

Meeting creation, update and deletion are **not** part of the current read-only acceptance. Evaluate independently and request explicit operator approval before adding write scopes or modifying any account (sandbox first).

### Increment D — Paid four-host meeting verification

After sandbox service acceptance, perform a separately approved, quiet-window read-only test of the four licensed production Zoom hosts, with host mapping kept in protected configuration. It does not authorize webinar calls, cloud-recording changes, or four-channel local recording automation.

### Deferred phase — Webinars

No webinar GET/POST requests or webinar-specific webhook subscriptions during the meetings phase. Reopen explicitly only after the meetings milestone is signed off; Basic sandbox cannot validate real webinar entitlements.

## Acceptance criteria for Increment A

- [ ] One account Basic sandbox is the only allowed tenant for local PoC; deliberate fail-closed on 0 or 2+ active users and on non-Basic type.
- [x] Authenticated local GET meeting-list endpoint returned count=1 (operator evidence; allowlist code committed, separate response-shape security audit pending).
- [x] Authenticated local GET meeting detail returned PASS for sandbox meeting (operator evidence); unit checks for listed ID present, negative runtime case pending.
- [ ] No Zoom host credentials, meeting join links, account IDs, passwords or API response bodies exposed via UI, API errors or logs.
- [ ] Unauthenticated local requests rejected; localhost-only binding documented and enforced by launcher.
- [ ] No webinar API calls in any test or runtime path; regression tests catch accidental calls.
- [ ] Mock-based tests verify token expiry, credential isolation, failures, pagination and response sanitization.
- [x] Operator executed end-to-end local sandbox read-only API client, confirming list count=1 and individual detail GET PASS, with redacted summary (2026-11-14).
- [ ] No change to existing paid Zoom organization apps, meetings, webinars or cloud recording.

## Immediate operator step

Nothing needs to be changed in the Zoom portal now. The initial FastAPI sandbox-local prototype is at `backend/meetings_api.py`, with implementation and eight new offline tests. Refer to [18-MEETINGS-LOCAL-SERVICE-RUNBOOK.md](18-MEETINGS-LOCAL-SERVICE-RUNBOOK.md) to install dependencies, run the expanded 23-test suite and launch an explicitly localhost-only service. The operator has confirmed successful authenticated HTTP list and detail GETs on Windows; the operator reports all 23 offline tests PASS; the negative authorization check remains pending. The operator's latest `meetings=1, meeting detail=PASS` result establishes the meeting API baseline. The implementation team should build/test Increment A in the repository, then provide a simple Windows command sequence for running the local service.

**Official references**

- S2S OAuth grant and token lifetime: https://developers.zoom.us/docs/integrations/oauth/
- List and get meeting endpoints/scopes: https://developers.zoom.us/docs/api/meetings/
- FastAPI header-auth options: https://fastapi.tiangolo.com/reference/security/

## Operator testing update — 2026-11-14

The operator confirmed that **all 23 currently committed offline unit tests passed** on Windows after the local authenticated Meetings API client had already reported list count=1 and meeting detail PASS. This is operator-reported test execution, not CI attestation. Live negative authentication/unauthorized access behavior and production hardening remain pending. Do not treat the sandbox localhost PoC as production ready.
