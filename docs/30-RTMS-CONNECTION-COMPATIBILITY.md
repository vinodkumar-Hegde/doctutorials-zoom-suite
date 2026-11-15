# ADR-030 — Zoom RTMS protocol compatibility and readiness transparency

**Date:** 2026-11-15. **Status:** Implemented and tested offline; no production Zoom entitlement or live media verified.

RTMS receiver improvements: accept `meeting.rtms_started`/`meeting.rtms_stopped` in both `payload` and `payload.object`; select permitted Zoom-domain alternatives from comma-delimited WSS endpoints; initialize signaling `sequence` to 1; send the single client-ready acknowledgement only after three independent audio, camera and desk-share handshakes; reject lack of media scopes; expose sanitized connection/permission state to the authenticated local dashboard. Add a read-only Windows preflight command. Never return Zoom app secrets, bearer tokens, meeting IDs or raw events through the browser. Keep test media clearly labeled.

References: https://developers.zoom.us/docs/rtms/event-reference/universal-events/ ; https://developers.zoom.us/docs/rtms/meetings/quickstart-rest-api/ ; https://developers.zoom.us/docs/rtms/troubleshooting/

Remaining: account Developer Pack and RTMS app enablement; real in-meeting packet verification, reconnect/pause/gap handling, stable faculty video selection, secure mapping for four simultaneous Zoom meeting IDs, 8-hour load test, verified local/NAS production archive. Offline tests do not constitute a live Zoom proof.
