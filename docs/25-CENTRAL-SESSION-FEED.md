# ADR-025 — Read-only Mac Admin schedule bridge to Windows Central Controller

**Date:** 2026-11-15  
**Status:** DEVELOPMENT PROTOTYPE; end-to-end tested in a local isolated environment, not on operator Mac/Windows LAN.

## Problem
The Mac HTTPS Admin/Faculty demo and Windows Central Controller were two separate loopback-only applications. The Windows interface showed four recorder slots without any Admin class assignments. This is not evidence of a Zoom live session or recorder capability.

## Decision
Implement an explicit, opt-in **read-only LAN HTTPS schedule bridge** on the Mac (separate from the existing 8443 service), with authenticated, certificate-pinned polling from Windows. The existing Mac Admin database, faculty login, meeting SDK credentials and Windows local recording processes remain untouched.

Only seven fields may cross to Windows: `sessionId`, `facultyId`, `course`, `subject`, `topic`, `startsAt`, `endsAt`. The Mac bridge reads SQLite with `mode=ro`. Neither Zoom meeting ID, passcode, joining information, JWTs nor student data are exposed. Windows pins the exact SHA-256 leaf TLS certificate **before** transmitting the long random/unique pairing secret; the client accepts only a private LAN IPv4 HTTPS endpoint and does not follow redirects. It fails closed when the bridge is unavailable. The Windows Controller HTTP listener remains on `127.0.0.1:8780`.

The pairing token is currently saved inside the Windows operator's per-user `%LOCALAPPDATA%/DocTutorials/session-feed.json` file. This is **development-only**, not a suitable enterprise credential vault. Production must move to DPAPI or Credential Manager, identity-aware access, firewall allowlists, and rotation.

## Scope / limitations
This feature gives the operator **Admin-scheduled sessions** inside Windows, with metadata pre-filled for an explicitly selected recorder channel. It does **not** join a Zoom meeting, detect whether a meeting is truly live, obtain media, or prove recording. Test channels still generate labeled synthetic media.

The installed Visual Studio C++ is a build prerequisite, not the Zoom Plugin SDK or Meeting SDK. Zoom's current Windows Meeting SDK documentation specifies raw media callbacks but prohibits unattended bots/AI notetakers; a permitted media acquisition path must be confirmed. Zoom RTMS is a possible authorized transport requiring credits and separate enablement; it is not cloud recording. These feasibility conditions block the final automatic Zoom recorder. No production Zoom settings are modified.

## Acceptance evidence
- 27 Python test cases in local Linux test environment PASS; includes four independent synthetic encoder jobs, authenticated controller API, one HTTPS certificate-pinned read-only Mac bridge with real SQLite rows, rejection of incorrect fingerprint/token, whitelist of allowed metadata, and fail-closed behavior.
- Windows `node --check` of `web/app.js` syntax PASS on development machine.
- **Operator Mac/Windows LAN end-to-end check pending.** One authorized live meeting's screen+video+audio media, four real concurrent Zoom recordings, iPad full-screen Goodnotes share and NAS production verification remain pending.

## References
- https://developers.zoom.us/docs/meeting-sdk/windows/get-started/download/
- https://developers.zoom.us/docs/meeting-sdk/windows/default-ui/advanced-features/raw-data/
- https://developers.zoom.us/docs/rtms/
