"""Read-only, deterministic automatic channel planning for ORIGINAL Admin classes.

No new class records, passwords, Zoom IDs, or silent Zoom joins.  Planning is not
proof of a live Zoom meeting and cannot enable a synthetic Zoom recording.
"""
from __future__ import annotations
import time

ACTIVE = {'starting', 'recording', 'stopping', 'finalizing'}


def enrich_admin_schedule(snapshot: dict, channels: list[dict], *, now: int | None = None):
    """Return copied schedules/channels with non-overlapping 4-slot reservations.

    Assignments are deterministic based on start time and immutable session IDs.
    Same-channel meetings must not overlap; exceeding capacity is explicit.
    No assignment is written back to the original Admin database.
    """
    now = int(time.time()) if now is None else int(now)
    plan = {k: [] for k in ('1','2','3','4')}
    output = dict(snapshot)
    enriched = []
    for original in sorted(snapshot.get('sessions', []), key=lambda s:(s['startsAt'],s['sessionId'])):
        item = dict(original)
        item['plannedChannel'] = None
        item['assignmentState'] = 'capacity_exceeded'
        item['zoomMediaConnected'] = False
        for channel_id, schedule in plan.items():
            if all(item['startsAt'] >= prev['endsAt'] or item['endsAt'] <= prev['startsAt'] for prev in schedule):
                item['plannedChannel'] = channel_id
                item['assignmentState'] = 'reserved'
                schedule.append(item)
                break
        enriched.append(item)
    output['sessions'] = enriched
    channel_view = []
    for original in channels:
        c = dict(original)
        assigned = plan.get(str(c.get('channel')), [])
        visible = [s for s in assigned if s['endsAt'] > now]
        visible.sort(key=lambda s:(0 if s['startsAt'] <= now else 1, s['startsAt'], s['sessionId']))
        candidate = visible[0] if visible else None
        c['assignedSession'] = (dict(candidate) if candidate else None)
        c['zoomMediaConnected'] = False
        config_ok = (c.get('configured') and
                     'TEST MEDIA' not in str(c.get('sourceMode','')).upper())
        c['configuredInput'] = bool(config_ok)  # Source config is NOT Zoom presence.
        c['captureReady'] = False  # Real Zoom feed has NOT been verified.
        channel_view.append(c)
    output['channels'] = channel_view
    output['assignmentPolicy'] = 'automatic_nonoverlapping_four_channels'
    output['mediaState'] = 'zoom_not_connected'
    return output


def selected_session(plan: dict, session_id: str, *, now: int | None = None) -> dict:
    """Only select an actual imported session in its scheduled time window."""
    from engine import RecorderError
    if not isinstance(session_id, str) or not session_id:
        raise RecorderError('Select an imported Admin session.')
    matches = [s for s in plan['sessions'] if s['sessionId'] == session_id]
    if len(matches) != 1:
        raise RecorderError('This session is not present in the imported Admin schedule.')
    item = matches[0]
    if not item['plannedChannel']:
        raise RecorderError('All four channels are reserved by overlapping classes.')
    now = int(time.time()) if now is None else int(now)
    if not (item['startsAt'] <= now < item['endsAt']):
        raise RecorderError('The class is outside its scheduled window; no live Zoom status is available.')
    return item
