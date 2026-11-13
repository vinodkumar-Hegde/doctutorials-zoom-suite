# Project Work Log

## 2026-11-13 — Kickoff
**User-confirmed:** four Zoom host accounts under one administrator; one concurrent class per host; capacities differ; faculty laptops and some laptop+iPad; Windows office system expected to record at least four different live sessions; automatic cloud backup for all; faculty must not be given host Zoom credentials; custom iPad app desired; GitHub Markdown project history desired.

**Completed:** Initial local documentation skeleton covering requirements, architecture, Zoom configuration, roles/security, recording flows, iPad, Windows workers, data model, roadmap, risks, and operational runbooks.

**Not yet done:** No Zoom account settings changed; no OAuth apps created; no GitHub remote selected/pushed; no code deployed; no real local or cloud recordings tested.

**Immediate next action:** In Zoom Admin, confirm the four host accounts and enable account/group-level automatic **cloud** recording; check existing webinars. Record outcomes in `docs/ZOOM-CONFIG-CHECKLIST.md`.

## 2026-11-13 — Milestone status and GitHub publication request
**Operator-reported completed:** Milestone 1 Zoom automatic cloud recording settings have been implemented. Do not claim recording quality, all-account coverage, storage adequacy, or recoverability independently verified until acceptance evidence is collected.

**Documentation changes:** Project status and cloud-recording checklist updated; repository publication instructions added.

**Repository publishing:** Requested creation of a dedicated private GitHub repository and push of the v0.1 project. At this stage there is no repository in the connected GitHub account by that name, and the available GitHub integration can write to existing repositories but has no repository-creation action. This is a publishing blocker, not a completed push.

**Next action after repository creation:** Commit/push the full documentation tree, preserve privacy, and start Gate 2 Server-to-Server OAuth read-only developer configuration.

## 2026-11-13 — GitHub publication
- Private repository: `vinodkumar-Hegde/doctutorials-zoom-suite`.
- Published 21 baseline v0.1 documentation and configuration files to `main`.
- Milestone 1 cloud recording was reported implemented by the operator; evidence and per-host validation remain open.
- Next: Gate 2, developer app and read-only Server-to-Server OAuth.

## 2026-11-13 — Milestone 2 S2S OAuth guidance started
- Retrieved current `AGENTS.md`, architecture, roadmap and developer-app guide directly from private GitHub repository, plus requirements/risks/references/work log.
- Verified official Zoom S2S app creation path, role prerequisite, granular read scopes, activation requirement, token grant, and webhook endpoint security requirements.
- Added [`15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md`](15-MILESTONE-2-S2S-OAUTH-RUNBOOK.md) with staged admin actions, scope matrix, webhook deferral and acceptance checklist.
- Operator asked to create `DocTutorials-Backend` in Zoom Marketplace; no app creation/activation or access token/API response observed yet.
- Milestone 1 remains operator-reported implemented with independent evidence pending. No changes to Zoom production settings.
- Next: operator confirms Developer Portal app created, then assist with Information → Scopes → Activation, without collecting credentials.

## 2026-11-13 — Milestone 2: OAuth application created (operator report)
- Operator confirmed `DocTutorials-Backend` has been created as a **Server-to-Server OAuth** app in the Zoom Developer Portal and the configuration pages are visible.
- Guided completion of **Information** (short description, organization name, authorized developer contact), **Feature** (defer webhooks), and five granular admin **read-only** scopes for users, meetings and webinars.
- Documentation checked against current official Zoom create-app and granular scopes pages; links retained in `docs/13-OFFICIAL-REFERENCES.md`.
- No Zoom secret, token, account ID, live API response, or credential screenshot received. No API or webhook calls made. App activation and scope selection are **not yet confirmed**; next step is operator confirmation followed by safe activation/verification.
- Milestone 1 cloud recording remains operator-reported implemented; no production settings changed in this step.

## 2026-11-13 — Milestone 2: Information and scopes completed (operator report)
- Operator replied 'done' to the step covering Zoom app **Information** and the five initial **admin read-only** scopes for `DocTutorials-Backend`; marked both operator-confirmed, not independently audited.
- Current Zoom documentation checked again: activation is required to issue usable account-credentials OAuth tokens. Admin-level permissions may be affected by future changes to the app owner's Zoom role.
- Next operator action: open **Activation** and activate only if validation is clear and no unexpected permissions are requested. Do not share Account ID, Client ID, Client Secret or tokens. Webhook setup, server-side credential vault, token request and four-host API test are pending.
- No Zoom settings were changed by the assistant and no Zoom API requests were made.

## 2026-11-13 — Milestone 2: S2S OAuth activated (operator report)
- Operator confirms `DocTutorials-Backend` Server-to-Server OAuth app **activated** successfully after five read scopes and Information completed.
- No app credentials, tokens or tenant data have been provided to the assistant; no live token request or API call has been performed.
- Started a stdlib-only, interactive Windows-compatible four-host API smoke test, with hidden credentials, GET-only Zoom resource calls, host alias output, fail-closed pagination/error handling and local tests.
- Next: publish and run the smoke test on an authorized machine, then record redacted outcome. HTTPS webhooks and production secret vault remain separate pending steps.

## 2026-11-13 — Milestone 2: Secure OAuth four-host test committed
- Added `backend/zoom_s2s_smoke_test.py`: Python 3.10+ stdlib-only token exchange, credential entry via hidden prompts, fixed Zoom HTTPS endpoints, read-only GET resource queries, pagination, explicit four-host selection and sanitized output.
- Added `tests/test_zoom_s2s_smoke_test.py`. Nine mock-based unit tests passed in isolated local runtime (request methods, Basic/Bearer handling, pagination, input selection, error sanitization, fail-closed JSON, path restrictions).
- Added Windows operator runbook `docs/16-MILESTONE-2-SECURE-API-SMOKE.md`. Updated supporting setup, roadmap and official reference documents.
- Operator has **not** provided secrets and has **not** yet reported live API results. Authentication and four-host retrieval are therefore pending tenant verification, as are production secret storage and webhook endpoint.
- Next: operator runs read-only test locally, shares only sanitized outcome and counts. Keep cloud recording settings unchanged.

## 2026-11-14 — Question: separate free Zoom sandbox
- Reviewed official Zoom product and developer documentation. Basic accounts can host ordinary meetings and make native desktop local recordings; webinars and Zoom cloud recording are paid features; RTMS is unsupported on Basic.
- Recommended, as a **proposal only**, isolating the first API and SDK development exercises in a separate Basic Zoom organization rather than touching live account configurations. Official S2S creation prerequisites mention a Zoom account and correct roles/scopes; exact Basic account app-entitlement must be checked in the developer portal.
- Important constraint: the existing four-host smoke test requires exactly four eligible paid/on-prem users; it **cannot pass against a standalone single-user free sandbox without a deliberately separate single-user test path**. Do not pretend it validates four production hosts.
- Meeting SDK apps joining meetings outside the SDK developer organization may require Zoom review and ZAK/OBF attribution per current Zoom docs; validate before integrating cross-account test flows.
- No sandbox has yet been created or chosen; no Zoom settings or existing developer apps were changed.

## 2026-11-14 — Screenshot review: Developer App Feature page
- Reviewed operator screenshot of `DocTutorials-Backend` **Feature** page. Event Subscriptions visible as OFF, matching the current Milestone 2 plan.
- Screenshot exposed the app's Webhook Secret Token; **did not copy, commit, or log its value**. Instructed operator to **Regenerate** only the webhook secret before future webhook integration and to mask secrets in any later screenshots. Rotation not yet confirmed.
- The screenshot does not independently verify the five saved OAuth scopes or live API response. Operator previously confirmed app activation; API smoke test remains pending.
- No change to existing Zoom meetings, webinars, or cloud recording settings; no secret rotation or Zoom action performed by the assistant.

## 2026-11-14 — Windows local setup blocker: Git and Python commands not found
- Operator ran the initial Windows PowerShell commands on `C:\Users\PC`. `git` and `py` were not recognized, so the repository was not cloned and no Python tests executed on this Windows workstation.
- Advised installing Git for Windows and Python 3.13 with `winget` (or official installers), closing/reopening PowerShell, verifying `git --version`, `py --version` / `python --version`, then cloning the private repository and running the offline unit tests.
- **No evidence yet** that Git/Python were installed, the repository cloned, offline tests passed on Windows, or live Zoom API credentials/test were used. Zoom production configuration remains unchanged.

## 2026-11-14 — Windows Python installation confirmed; Git still missing
- Operator reports Python 3.13.17 Windows installer completed successfully, but current `python --version` resolves to **Python 3.11.9**; Python 3.11 is compatible with our stdlib-only OAuth smoke test.
- The `py` launcher is not on PATH; it is optional because `python` works. Future Windows test instructions should use `python -m unittest discover -s tests -v` and `python backend\\zoom_s2s_smoke_test.py`.
- `git --version` is still not recognized. Next: reopen PowerShell to refresh PATH; if still absent install Git (`winget install --id Git.Git -e --source winget`), reopen PowerShell and verify. Fallback direct executable path: `C:\\Program Files\\Git\\cmd\\git.exe` (only if it exists).
- No successful clone or local test evidence yet; Zoom S2S app remains operator-confirmed activated, live API verification pending.

## 2026-11-14 — Git installed according to winget but PowerShell PATH unresolved
- Operator reports `winget install --id Git.Git -e --source winget` says an existing Git installation is present and no upgrade is available, but `git --version` remains unrecognized in the current PowerShell session.
- `python --version` returns Python 3.11.9; supported by our smoke test.
- Recommended checking `Test-Path "C:\\Program Files\\Git\\cmd\\git.exe"` and running Git via absolute path; if present, append that directory to the PowerShell session PATH temporarily, then clone the private repository and run nine offline tests.
- Not yet confirmed Git executable path, clone, test results or live Zoom API success. No Zoom settings changed.

## 2026-11-14 — Windows development environment now operational (operator evidence)
- Operator verified `C:\Program Files\Git\cmd\git.exe` exists and reports **Git 2.56.0.windows.4**. Current PowerShell session PATH was updated with `C:\Program Files\Git\cmd`, after which `git --version` succeeded. This PATH modification is session-only unless the user later persists it.
- `python --version` reported **Python 3.11.9**, compatible with the S2S smoke test; `py` launcher is unnecessary.
- Operator successfully cloned the private `vinodkumar-Hegde/doctutorials-zoom-suite` repository to `C:\Users\PC\doctutorials-zoom-suite`.
- Operator ran `python -m unittest discover -s tests -v`: **9 tests passed**, with no failures. This is independent confirmation of offline test success on the intended Windows workstation.
- The operator also checked alternate Git paths that returned False; this is expected because the installed binary is under Program Files.
- **Live Zoom tenant OAuth/API smoke test has NOT been reported run**. Next: with private inputs on a trusted workstation, run `python backend\zoom_s2s_smoke_test.py` against the intended Zoom tenant only with operator authorization. This four-host script is for a tenant with >=4 eligible users, not a standalone one-user free sandbox. Avoid active-class windows due to shared API quotas, do not share secrets or raw account identifiers.

## 2026-11-14 — First actual Zoom S2S OAuth request: success, four-host check blocked
- Operator ran `python backend\zoom_s2s_smoke_test.py` on the Windows workstation. First run was aborted because the Client Secret prompt was left empty; this is not an API/authentication failure.
- Second run returned **OAuth token request: PASS** and **List active users: PASS (1 total)**; **Eligible paid/on-prem host candidates: 0**, and **RESULT NOT PASSED: expected at least 4**.
- Therefore the S2S grant and `GET /users` are **live-verified** for the supplied credentials, but the connected tenant contains just one active user with no eligible paid hosts. Whether this was the intended free sandbox or incorrect production app/organization is **not established**. **No four-host read, webinar list, meeting list or detail success has been confirmed.** No OAuth secrets, tokens, account IDs or host identities shared.
- Added opt-in `--sandbox-single-user` mode to `backend/zoom_s2s_smoke_test.py`. It accepts exactly one active user regardless of Basic license, tests meeting GET only and explicitly marks webinar/four-host verification as pending. The original default four-host validation is unchanged. Added four unit tests (total now 13); user-side execution of updated tests is pending.
- Next: operator `git pull`, run 13 offline tests and `python backend\zoom_s2s_smoke_test.py --sandbox-single-user` if intending a separate one-user sandbox; otherwise inspect which Zoom account/app generated these credentials before any four-host retry. Maintain existing live Zoom account settings unchanged.
