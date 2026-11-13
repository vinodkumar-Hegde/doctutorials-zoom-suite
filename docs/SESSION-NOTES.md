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
