# ADR-029 — Direct Zoom RTMS Windows media ingress, gated by entitlement and session identity

**Date:** 2026-11-15  
**Status:** Experimental; implementation + offline transport/encoding tests only; Zoom RTMS end-to-end NOT verified.

## Problem

The Windows system correctly imports the original Admin assignments and automatically reserves one of four FFmpeg channels, but all existing channel media is still synthetic. The user does not want Mac bridges, browser screen capture, OBS, Zoom Cloud Recording, or manual duplicate class entry.

## Decision

Add an **optional** Zoom RTMS client using direct `wss://` WebSocket protocol. The Windows process initiates the Event WebSocket connection (no inbound public endpoint), validates Zoom host domains for RTMS signaling/media URLs, performs HMAC handshakes, and writes actual received Zoom RTMS audio, active-speaker video and screen-share packets into separate files. Real media tracks are combined with DocTutorials logo, teaching screen, camera PIP and metadata footer into an H.264/AAC MP4. MP4 verification and existing local/NAS storage catalog logic are shared. Fail closed for synthetic demo mode, missing tracks, invalid packets, or ambiguous class assignment. Never hardcode, persist, or log Zoom credentials.

RTMS support remains **disabled by default**; explicit command `--config config.json --rtms` requires an RTMS-capable OAuth app, active Developer Pack credits, approved permissions, event subscription and host/participant consent. Normal `start-demo-windows.bat` is unchanged and cannot access Zoom media.

## Remaining blockers and risks

1. No RTMS app credentials/credits have been verified; no live Zoom meeting handshake, real-media source, Windows integration or production recordings verified.
2. The current imported schedule deliberately omits Zoom meeting IDs. The receiver associates a stream to a class only if exactly one class is scheduled now. With two or more overlapping sessions, it **refuses to record** rather than misroute streams. Four independent meetings require the authoritative Admin backend to securely store and match Zoom meeting identity without exposing it to the browser.
3. The packet compositor uses nominal H.264 25fps and raw PCM 16kHz. It does **not** yet repair timestamp jitter, audio buffering offset, gaps, video off/mutes, changes of active speaker, H.264 codec changes, 8-hour uptime or out-of-order/reconnected media. RTMS gives **active speaker video**, not verified *faculty* video. The current PIP cannot be called faculty-specific until stable participant selection is implemented.
4. Public Zoom Meeting SDK Windows usage policy prohibits unattended bot use; RTMS is the documented automated alternative. Zoom's own RTMS SDK may not ship native Windows binaries, but official `zoom/rtms-samples` documents a direct WebSocket transport requiring only a compatible WebSocket client.
5. Windows credentials stored in process environment must be supplied from approved enterprise credential storage at deployment. No Zoom account settings or billing changes are made by this code.

## Test evidence

- Existing 59 offline tests plus 7 RTMS protocol/payload/composition tests = **66 local tests PASS** on Linux developer environment. Synthetic FFmpeg H.264+PCM data wrapped in RTMS-style packets was composed into a valid branded H.264/AAC MP4 and registered in Storage Center. This **does not** validate the real Zoom RTMS protocol handshakes, media fidelity, Windows interoperability or stream credits.
- `python -m py_compile` of new modules PASS; Windows run pending.
- Next acceptance step after RTMS enablement: one consented sandbox meeting with known course/topic, screen share + faculty video + mixed audio; inspect A/V sync, recording duration, logo, channel identity and Storage Center MP4. Then implement authoritative multi-meeting identity routing, then attempt 2 / 3 / 4 independent actual meetings.

Sources: https://developers.zoom.us/docs/rtms/meetings/getting-started/ ; https://developers.zoom.us/docs/rtms/meetings/media/ ; https://github.com/zoom/rtms-samples ; https://developers.zoom.us/docs/meeting-sdk/windows/get-started/download/
