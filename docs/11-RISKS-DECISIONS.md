# Architecture Decisions, Risks and Unknowns

Date: 2026-11-13. Status terms: `ACCEPTED`, `PROPOSED`, `OPEN`, `REJECTED`.

## Decisions
- **ADR-001 [ACCEPTED]** Faculty use DocTutorials credentials and do not get Zoom host account passwords.
- **ADR-002 [ACCEPTED]** Automatic Zoom cloud recording is the safety backup for each of four Zoom host users.
- **ADR-003 [ACCEPTED]** Faculty may use laptop + iPad or laptop-only; iPad custom app is in project scope.
- **ADR-004 [PROPOSED]** Build backend using FastAPI/PostgreSQL and React portal.
- **ADR-005 [PROPOSED]** Use Windows Zoom Workplace + Plugin SDK for native local capture, subject to Gate 3 proof; then four isolated channels.
- **ADR-006 [OPEN]** Which Zoom app user/principal signs into each Windows recorder? Preferred: assigned host user in dedicated worker, pending account + UI automation tests.
- **ADR-007 [OPEN]** Windows isolation: four VMs on one server vs four physical workers.
- **ADR-008 [PROPOSED]** Cloud auto-recording remains independent/continuous even if local recording is paused by faculty.
- **ADR-009 [OPEN]** Webinar panelist joins through custom iPad Meeting SDK without individual Zoom login: test entitlement and invitation flow.
- **ADR-010 [ACCEPTED]** GitHub repository: private `vinodkumar-Hegde/doctutorials-zoom-suite`, published on 2026-11-13.
- **ADR-011 [ACCEPTED]** Milestone 1 cloud auto-recording is operator-reported implemented as of 2026-11-13; acceptance evidence remains pending. Do not reconfigure live Zoom settings simply to close paperwork.

- **ADR-012 [PROPOSED]** One internal Server-to-Server OAuth app for four Zoom hosts, with least-privilege read-only account scopes initially. Webhook subscriptions are deferred until a signed, validated, public HTTPS endpoint exists; cloud-recording read access added for archive implementation with explicit approval. No passwords or tokens shared with faculty. Operator app creation and API validation pending.

- **ADR-013 [PROPOSED]** Prefer a separate Zoom Basic organization as a nonproduction sandbox for API token/read-only meeting tests and initial native meeting/local-recording and iPad Meeting SDK experiments, subject to app entitlements. Never reuse production S2S credentials in a sandbox app; an S2S app's tokens access only its own Zoom organization. Basic does not provide webinar hosting or Zoom cloud recording, and a single free user cannot validate four concurrent licensed hosts. Preserve live-account acceptance gates for all paid features. The operator has not yet selected or created a sandbox.

## Top risks
| Risk | Severity | Mitigation |
|---|---|---|
| Plugin SDK missing reliable local record API/permission | Critical | Single-client proof; fallback explicit human operation or RTMS evaluation |
| Free sandbox is mistaken for full production parity | High | Keep 4-host, webinar and cloud backup acceptance tests on separately authorized paid staging/live accounts |
| Four Zoom Workplace VMs unstable / account conflict | Critical | Load tests, physical worker fallback |
| Webinar host cannot start fully unattended | High | Office-host startup design with manual supported fallback |
| iPad panelist joins SDK as attendee / cannot share | High | Real webinar POC before app build |
| Initial lecturer seconds missing | High | Prepare and start recording before faculty instruction; cloud auto backup |
| Cloud storage exhausted | High | Measure actual plan, alert on quota, archive and approved retention |
| Credential/PII leakage via GitHub/logs | Critical | Private repo, vault, ignore, secret scanning, RBAC |
| Webhook signing secret visible in shared screenshot (2026-11-14) | High | Rotate this app's webhook secret before subscriptions are enabled; never commit value; operator confirmation pending |
| Webhook latency/duplicates | Medium | Idempotency, state reconciliation, not relying on webhooks for first frame |
| Full-device iPad screens expose notifications | High | Faculty privacy checklist, Focus mode, in-app reminder |
| Network/storage failure damages video | High | Local SSD, file conversion handling, retries, safe recovery |

## Explicit unresolved assumptions
- Exact 4 host usernames, paid license features and mappings to webinar capacity.
- Exact Windows machine/VM deployment and Zoom client compatibility.
- Cloud quota, compliance and recording retention policy.
- Required output layout and whether additional audio/video tracks are necessary.
- Faculty join authentication/security restrictions enabled on Zoom account.
- Whether live teaching is always webinars or sometimes meetings (support both).

Change this register as soon as a test invalidates an assumption.
