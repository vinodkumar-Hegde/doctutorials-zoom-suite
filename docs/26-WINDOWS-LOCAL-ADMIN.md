# ADR-026 — Consolidate Admin scheduling on Windows Central Controller

**Date:** 2026-11-15  
**Status:** Implemented and locally tested; operator Windows verification pending. **Supersedes the Mac bridge of ADR-025 for the standalone Windows workflow.**

## Reason
The Mac-to-Windows schedule bridge required a separate Mac host, IP address, certificate and pairing secret, despite the operator's requirement that the central Windows PC independently manage Admin sessions, recording and storage. That bridge created unnecessary operational dependency. The operator explicitly rejected it and requested the all-Windows architecture.

## Decision
- Store Admin class assignments in Windows SQLite alongside the recorder's storage root; serve them from the same authenticated, loopback-only controller HTTP application (`127.0.0.1:8780`).
- Add authenticated Admin create/list/cancel APIs, schedule form, four-channel reservations, collision rejection and persistent status. Nothing records or joins Zoom merely because a session was scheduled.
- The recorder now loads `LocalSessions` and **does not initialize or require** any Mac session feed. Historical Mac-bridge files are retained only as obsolete development artifacts, not installed in the standalone ZIP or required for operations.
- No Zoom ID/passcode, SDK secret, client token or student details are in the schedule database or response. The storage root and its SQLite files remain local, outside Git.
- Keep all playback, channel isolation and NAS behavior unchanged; continue to distinguish `TEST MEDIA` from live Zoom capture.

## Acceptance evidence
- 40 Python tests passed in a local Linux environment, including the existing four-process recording-engine checks and 13 local Admin schedule/auth/overlap/persistence tests; JavaScript syntax check passed.
- End-to-end verification on operator Windows remains pending.
- **Not implemented/verified:** Zoom Meeting SDK connector, observed Zoom meeting/live status, independent class media acquisition, true four-Meeting recording, faculty iPad/desktop session synchronization, full-device Goodnotes screen broadcast, or production security hardening. These remain blockers to full product acceptance.

## Follow-up
For an enterprise rollout, replace the local-only demo credentials with a hardened Windows-hosted service, TLS ingress, persistent faculty/admin identity, managed secret storage, authorized Zoom capture SDK adapter, recording consent flow and NAS capacity monitoring. Do not expose the current local HTTP controller over LAN or internet.
