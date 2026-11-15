# Identity, Roles and Security

## Identities
1. **Zoom organization admin:** account configuration, billing, licensed users, developer app management.
2. **Four Zoom host users:** licensed host identities; one simultaneous active session per host. Host credentials remain owned by operations.
3. **DocTutorials faculty:** separate application user identity, sessions, and allowed controls. Never receives host account password or ZAK.
4. **DocTutorials operator/admin:** manages schedules, worker state and recordings with role-based audit trail.
5. **Recorder worker:** authenticated machine identity mapped to one Zoom host/session channel; not a generic elevated principal.

## Authorization principles
- Backend verifies faculty assignment for every operation and delivers only session-scoped join options.
- Webinar panelist-specific joining links/tokens are considered **sensitive bearer invitations**; avoid exposing them in logs or shared repositories. A guest webinar join may require different Zoom settings from authenticated panelist joining; test explicitly.
- The faculty iPad and laptop can be separate webinar participants; they should not share the exact same single-use panelist invitation.
- Office operations must be able to start webinars under authorized host credentials, or provide a documented human host startup fallback.
- Recording and cloud sharing comply with internal notice/consent and privacy policy.

## Security controls
- TLS for all APIs and webhooks; validate Zoom webhook origin using official signature/secret procedures.
- OAuth tokens in vault, access limited by service; rotate and audit.
- Signed short-lived tokens for app sessions; server-side revocation.
- TLS and machine credentials for worker API.
- Strong audit trail: who scheduled, started/stopped, archived, downloaded/deleted.
- Private GitHub repository, protected main branch, code review, dependency scanning, secret scanning.
- Do not expose signed cloud download links or direct NAS paths to unauthorized users.
- Do not automatically delete original cloud file before verified local archival.


## 2026-11-15 — Basic sandbox first-party faculty password pilot
The operator explicitly selected **DocTutorials-managed static password** for initial one-faculty Zoom Basic Meetings/iPad testing rather than an external identity platform. Implementation is staged, default-OFF, **not a production authentication system**. Backend provides salted scrypt password hash stored in private mode-0600 local config, five-failed-attempt lockout per 15 minutes, and in-memory, revocable/expiring opaque bearer sessions lasting 15 minutes. Faculty join requires a distinct server-owned sandbox session assignment and server-signed participant-only Meeting SDK JWT.

Do not hardcode a password in the iPad, distribute one password among multiple real faculty, accept client-supplied faculty IDs as identity proof, embed SDK Client Secrets or Zoom host credentials, or reuse the existing localhost operator API as a public faculty API. Protected HTTPS + correct trusted proxy scheme, ingress rate limiting, no credential-bearing logs, and backend-only secret storage remain prerequisites to activation. See `docs/22-FIRST-PARTY-STATIC-PASSWORD-AUTH.md`.
