# Gate 2B — Meetings-Only Secure Backend Implementation

**Date:** 2026-11-14
**Decision:** ADR-014 — Implement and accept Zoom Meetings integration before starting webinar integration.
**Scope status:** Planned. This document is an implementation/acceptance plan, **not** a deployed or completed backend.

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

### Increment A — Local read-only service (next)

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
- [ ] Authenticated GET meeting-list endpoint returns the single sandbox meeting using only an allowlisted response schema.
- [ ] Authenticated GET meeting-detail endpoint checks the requested ID belongs to the selected host; unknown IDs rejected.
- [ ] No Zoom host credentials, meeting join links, account IDs, passwords or API response bodies exposed via UI, API errors or logs.
- [ ] Unauthenticated local requests rejected; localhost-only binding documented and enforced by launcher.
- [ ] No webinar API calls in any test or runtime path; regression tests catch accidental calls.
- [ ] Mock-based tests verify token expiry, credential isolation, failures, pagination and response sanitization.
- [ ] Operator executes an end-to-end local sandbox run and reports only redacted summary.
- [ ] No change to existing paid Zoom organization apps, meetings, webinars or cloud recording.

## Immediate operator step

Nothing needs to be changed in the Zoom portal now. The operator's latest `meetings=1, meeting detail=PASS` result establishes the meeting API baseline. The implementation team should build/test Increment A in the repository, then provide a simple Windows command sequence for running the local service.

**Official references**

- S2S OAuth grant and token lifetime: https://developers.zoom.us/docs/integrations/oauth/
- List and get meeting endpoints/scopes: https://developers.zoom.us/docs/api/meetings/
- FastAPI header-auth options: https://fastapi.tiangolo.com/reference/security/
