"""Meetings-only read model for the one-user Zoom Basic sandbox.

No HTTP framework dependency. This module never calls webinar or write APIs.
It is intentionally sandbox-only; production four-host access requires a separate
reviewed implementation and explicit approval.
"""

from __future__ import annotations

import threading
import time
from urllib.parse import quote

from backend.zoom_s2s_smoke_test import SmokeTestError

TOKEN_RENEW_SECONDS = 20 * 60


def safe_meeting(meeting: dict, ordinal: int) -> dict:
    """Return an explicit allowlist; never return Zoom join URLs or passcodes."""
    out = {"ref": ordinal}
    for field in ("topic", "start_time", "timezone", "status"):
        value = meeting.get(field)
        if isinstance(value, str):
            out[field] = value[:300]
    duration = meeting.get("duration")
    if isinstance(duration, int) and not isinstance(duration, bool) and 0 <= duration <= 1440:
        out["duration"] = duration
    return out


class SandboxMeetingsService:
    """In-memory, single-user Basic-account read service.

    Calls must originate behind a separately authenticated local HTTP boundary.
    The service serializes Zoom API calls and holds only an in-memory token.
    """

    def __init__(self, zoom_client, clock=time.monotonic):
        self._zoom = zoom_client
        self._clock = clock
        self._lock = threading.RLock()
        self._sandbox_user_id: str | None = None
        self._reauth_at = 0.0

    def _ensure_sandbox(self) -> None:
        now = self._clock()
        if not self._sandbox_user_id or now >= self._reauth_at:
            self._zoom.authenticate()
            self._reauth_at = now + TOKEN_RENEW_SECONDS
            users = self._zoom.list_users()
            # Basic Zoom user type == 1; fail closed for paid, multi-user and empty tenants.
            if (
                len(users) != 1 or
                users[0].get("type") != 1 or
                not isinstance(users[0].get("id"), str) or
                not users[0]["id"]
            ):
                self._sandbox_user_id = None
                raise SmokeTestError("Local Meetings service requires one Basic sandbox user.")
            self._sandbox_user_id = users[0]["id"]

    def _list_raw(self) -> list[dict]:
        self._ensure_sandbox()
        assert self._sandbox_user_id is not None
        return self._zoom.list_meetings(self._sandbox_user_id)

    def list_meetings(self) -> list[dict]:
        with self._lock:
            return [safe_meeting(m, n) for n, m in enumerate(self._list_raw(), start=1)]

    def get_meeting(self, ordinal: int) -> dict | None:
        with self._lock:
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
                return None
            items = self._list_raw()
            if ordinal > len(items):
                return None
            listed_id = items[ordinal - 1].get("id")
            if not isinstance(listed_id, (str, int)) or not str(listed_id).isdigit():
                raise SmokeTestError("Meeting list returned an invalid meeting ID.")
            details = self._zoom.get(
                "/meetings/" + quote(str(listed_id), safe=""),
                purpose="Get sandbox meeting details",
            )
            if str(details.get("id")) != str(listed_id):
                raise SmokeTestError("Meeting detail does not match sandbox meeting list.")
            return safe_meeting(details, ordinal)
