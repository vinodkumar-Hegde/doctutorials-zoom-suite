# Roadmap and Acceptance Gates

Work proceeds gate by gate. Distinguish an operator report of implementation from objectively verified acceptance evidence.

## Gate 0 — Private repo + documentation
- [x] Architecture and product requirements baseline prepared locally.
- [x] Created **private** GitHub repository `vinodkumar-Hegde/doctutorials-zoom-suite` and published documentation (2026-11-13).
- [ ] Enable branch protection, secret scanning, PR reviews.
- [ ] Identify maintainer and approve initial ADRs.

## Gate 1 — Cloud safety backup
**Implementation status:** REPORTED COMPLETE by operator on 2026-11-13. **Acceptance status:** PENDING EVIDENCE. Do not reset/reconfigure the account just to repeat this milestone; collect redacted proof and close open checks.
- [ ] Confirm the four host users and their licenses in Zoom Admin (do not commit user IDs).
- [ ] Enable cloud recording and automatic recording to cloud at correct account/group level.
- [ ] Audit already-scheduled meetings and webinars, including recurring sessions.
- [ ] Test one meeting + one webinar (not practice mode).
- [ ] Confirm cloud file available, downloadable and expected layout.
- [ ] Measure capacity/retention and confirm privacy notice.
**Pass criteria:** Cloud backup works reliably on all four host users and can be recovered if local recorder fails. Unchecked lines above remain validation tasks, not claims that admin configuration was not performed.

## Test environment policy (proposal, 2026-11-14)
- [x] Use separate Zoom Basic sandbox for initial S2S token/GET and ordinary meeting/local-recording tests (operator confirmed credentials belong to Basic sandbox; live token and GETs passed 2026-11-14).
- [x] S2S app credentials belonging to separate Basic sandbox authenticated successfully (operator report 2026-11-14); exact sandbox app name not established. Do not copy production credentials into sandbox.
- [x] Implement explicit `--sandbox-single-user` read-only mode for one active Basic account (does not exercise webinar APIs or count as production acceptance).
- [x] Run one-user sandbox mode: OAuth token PASS, active users GET PASS (1), meeting list GET PASS (0), RESULT PASS (2026-11-14; operator-confirmed). Detail GET skipped due to no future meetings; webinar API not tested.
- [ ] Keep final four licensed-host mapping, webinar panelist, simultaneous recordings, and cloud safety backup tests on authorized paid staging or production account with explicit operator approval.
- [ ] For iPad Meeting SDK joining meetings hosted outside SDK developer account, verify Zoom's current review and ZAK/OBF requirements before choosing cross-account test setup.

## Current delivery sequence — operator-approved meetings first (2026-11-14)
1. **COMPLETED (read-only sandbox proof) — Basic sandbox meetings:** S2S authentication, user list, scheduled meeting list and individual meeting detail PASS for one sandbox meeting.
2. **COMPLETED — Basic sandbox read-only local API proof:** Authenticated loopback-only FastAPI list/detail GET passed, 23 offline tests passed, and unauthenticated GET correctly returned HTTP 401 (operator reports 2026-11-14). Security hardening, meeting writes/events and production deployment remain separate pending work.
3. **LATER — webinar integration:** Only after meeting integration acceptance, test webinars, panelists, scopes, lifecycle and any relevant recording flows on an authorized paid environment. No webinar API GET or webhook subscription in current integration phase.
4. **PRODUCTION ACCEPTANCE STILL REQUIRED:** Four licensed hosts, cloud backup, local recording and concurrency feasibility are not validated by the one-user Basic sandbox.

The default four-host read-only smoke test has been changed to **meetings-only**; its webinar calls are disabled in the active code path. The one-user sandbox mode remains meetings-only. Two new offline test cases were committed (15 total); the operator reran the suite and all **15/15 passed** (2026-11-14).

## Gate 2 — Developer backend
**Status (2026-11-14):** **BASIC SANDBOX LOCAL READ-ONLY MEETINGS POC PASSED**, including unauthenticated HTTP 401 and authenticated local FastAPI client path: local meetings GET PASS (count 1), detail GET PASS. The Windows operator confirmed **23/23 offline tests PASS** (2026-11-14, operator report). Production backend, write APIs, four-host production, webhooks and secret vault remain pending. Guides: [`15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md`](15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md) and [`16-MILESTONE-2-SECURE-API-SMOKE.md`](16-MILESTONE-2-SECURE-API-SMOKE.md). No real credentials have been shared with the assistant. The operator has verified live **sandbox meeting GET** APIs; webhook and production API tests have not been performed.
- [x] Create Server-to-Server OAuth app `DocTutorials-Backend` (operator-confirmed; ownership/tenant verification pending).
- [x] Complete app Information and add five least-privilege read-only admin scopes (operator-confirmed 2026-11-13; scope evidence pending).
- [x] Activate `DocTutorials-Backend` (operator-confirmed 2026-11-13; token exchange not independently checked).
- [ ] Provision account credentials to an approved backend vault (never GitHub/chat).
- [x] Implement secure local Python S2S OAuth + four-host read-only API smoke test; nine isolated offline unit tests passed (2026-11-13).
- [x] Operator cloned the private repo on Windows; confirmed Git 2.56.0, Python 3.11.9 and **9/9** offline unit tests passing (2026-11-14).
- [x] First LIVE S2S token exchange, `GET /users`, and (sandbox mode) user meetings-list GET completed on Windows: PASS using the separate free Zoom sandbox (1 active user, 0 meetings).
- [x] Added separate opt-in one-user Basic/sandbox smoke test mode; after meetings-only adjustments and two additional regressions, **15/15 offline tests passed** on operator Windows PC (2026-11-14).
- [x] Verify individual future meeting detail GET in sandbox: **meetings=1, meeting detail=PASS** (operator evidence 2026-11-14).
- [x] Commit an initial sandbox-only localhost FastAPI Meetings read-service prototype and 8 mock-based tests (2026-11-14; code unverified on operator machine; no deployment).
- [x] Operator launched sandbox-local FastAPI server at `http://127.0.0.1:8765` and then **successfully tested authenticated localhost GET /v1/meetings (count=1) and GET /v1/meetings/1** with the client (2026-11-14).
- [x] Authenticated localhost Meetings API client PASS (meetings=1, detail PASS, no webinar APIs), operator evidence 2026-11-14.
- [x] Operator reports all 23 expanded offline unit tests PASS (2026-11-14; summary not pasted, no independent CI verification).
- [x] Live localhost GET without `X-DocTutorials-Key` rejected with **HTTP 401** (operator-confirmed 2026-11-14).
- [x] Close **Gate 2B Basic-sandbox local read-only Meetings PoC** as passed (authentication, list/detail, 23 offline tests, unauthenticated 401). **Not a production security certification.**
- [ ] Formal production hardening, tenant-specific role controls, secret management, authorization abuse tests and deployment review remain pending.
- [ ] Rotate ephemeral localhost API session key by stopping/restarting local backend after sharing the two temporary keys in chat; do not share replacement key or place it in GitHub.
- [ ] Execute four-host live GET checks against the correct authorized four-host organization; record non-sensitive results only.
- [ ] Read four intended paid users and their future **meetings** using least-privilege scopes (production tenant read-only verification pending). Webinar API acceptance deferred.
- [ ] Validate HTTPS webhook and signed messages; dedupe events.
- [ ] Receive start/end and cloud recording completion events in test.
**Pass criteria:** API correctly maps sessions to host user, and cloud archive can download verified recordings.

## Gate 3 — Windows local native recorder feasibility (blocking)
**Stage 3A started 2026-11-14:** Official Windows Plugin SDK requirements, separate OAuth/scope and bundled PSDKTest demo reviewed; read-only environment/SDK-folder/MP4 container probe plus **12** offline tests committed (repository total **35**, new tests not yet operator-run). The probe **does not invoke SDK commands or record meetings**. See [Stage 3A runbook](19-GATE3-WINDOWS-PLUGIN-SDK-RECORDER-SPIKE.md).
- [ ] Operator runs expanded **35** offline tests and Windows workstation readiness probe; confirms actual Zoom Workplace version.
- [ ] Download compatible Windows Plugin SDK from a sandbox General App, following Zoom authorization rules; no production app changes.
- [ ] Build Zoom's official PSDKTest Release x64 and validate IPC OAuth connection on one authorized sandbox Windows Zoom Workplace client.
- [ ] Determine actual local recording permissions and supported start/stop/pause/resume controls (record every unavailable API explicitly).
- [ ] Independently verify final local MP4 container, playback, voice and screen share; no recordings committed to GitHub.
- [ ] Create Windows General App + Plugin SDK integration.
- [ ] Authenticate on one signed-in Zoom Workplace client.
- [ ] Prove authorized host session join, local start/stop and file confirmation.
- [ ] Test iPad + laptop content layout and laptop-only layout.
- [ ] Prove remote Start/Pause/Resume/Stop **only where SDK actually supports them**.
**Pass criteria:** One complete, independently confirmed local MP4 recording with correct media and permission model.

## Gate 4 — iPad SDK feasibility
- [ ] Setup iOS General App + Meeting SDK and short-lived backend signing.
- [ ] Join account-hosted webinar as authorized panelist without Zoom host password.
- [ ] Use ReplayKit extension to share Goodnotes/other app; confirm OS user consent.
- [ ] Faculty laptop camera/audio + iPad share present and recorded.
**Pass criteria:** iPad share + webinar join works on real faculty iPad, without distributing host credentials.

## Gate 5 — Four-channel load and reliability
- [ ] Run four concurrent webinar/meeting host users for test duration representative of classes.
- [ ] Independently start/stop recordings; verify separate identities and assets.
- [ ] Test pause/resume if available, disconnect/reconnect, CPU/disk/network faults.
- [ ] Measure output quality and archive transfer under load.
- [ ] Decide VM vs separate physical workers based on results.
**Pass criteria:** Four simultaneous complete local files plus four independent cloud backups with no cross-session leakage.

## Gate 6 — Product and production
- [ ] Faculty portal and operator dashboard, RBAC, monitoring, alerts.
- [ ] NAS archival + cloud backup sync, checksum verification, retention policy.
- [ ] iPad TestFlight, then approved distribution.
- [ ] CI/CD, rollback, runbooks, support, security assessment and training.
**Pass criteria:** End-to-end operator rehearsal and sign-off.
