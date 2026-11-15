# ADR-028 — Automatic Windows channel reservations from the original Admin database

**Date:** 2026-11-15  
**Status:** Implemented in code, locally tested; operator's Windows verification pending. **Zoom media connector absent.**

## Decision

Do **not** ask the user to re-enter classes or install another Admin portal. Read the existing imported DocTutorials Admin DB without modifications. For every scheduled class, deterministically reserve the first free channel among four, respecting half-open `[start,end)` time windows. Sequential classes reuse an available channel. Show a fifth overlapping session as `capacity_exceeded`; do not create a fake fifth recorder.

Return `plannedChannel` and `assignmentState` from the authenticated `/api/sessions` endpoint and `assignedSession` on each channel through `/api/channels`. Prefer an ongoing scheduled class to a future scheduled class when rendering. Historical reservations do not fill currently idle channel cards. Channel allocation is recomputed and is **not persisted**; if the Admin DB changes, future placements can change. This is an initial reservation planner, not a production scheduler or permanent worker ID assignment.

The existing class form has been removed since the prior correction. No Zoom meeting numbers, passcodes or Zoom credentials are serialized to the dashboard.

## Controls and limitations

A reservation never means a Zoom meeting is live. This version labels media as `zoom_not_connected` and keeps TEST MEDIA clearly separate. On the read-only Admin path, `POST /api/start-assigned` permits an operator-confirmed capture only for a scheduled imported session within its window with non-test, non-file configured inputs, using server-derived metadata; it never auto-joins or acquires Zoom streams. `POST /api/start` is rejected for original Admin session IDs. In a deployed system, recording authorization, real media identity and consent evidence require stronger verification before automation.

Zoom's official 2026 Meeting SDK policy is for interactive human use; RTMS for Meetings is the recommended route for unattended media capture and supports audio, video and screen share. Requires a separately enabled app/credits and tested media adapter. Four independent actual Zoom recordings, iPad Goodnotes share, Windows deployment and NAS end-to-end remain unverified.

## Evidence

59 local Python unit/integration tests passed on the build workstation, including original four synthetic media workers, source authorization rejection, channel planning, and real imported class metadata in the start call to a **fake** capture engine. JavaScript syntax checked with `node --check`. No Zoom live-media capture was tested. Windows user to test after updating repository.

References:
- https://developers.zoom.us/docs/meeting-sdk/windows/
- https://developers.zoom.us/docs/rtms/meetings/getting-started/
