"""Fail-closed authorization policy for iPad participation in one Zoom Basic sandbox meeting.

This is a domain service, NOT a public route or a faculty login mechanism.
Only a trusted authentication layer may instantiate AuthenticatedFaculty.
The assignment source must be server-owned; never accept assignments,
Zoom meeting numbers, display names, SDK credentials, or passcodes from the
iPad request body.

A future HTTPS endpoint must bind the authenticated identity to this service
and turn JoinDenied into a generic 403 without logging the sensitive ticket.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable

from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials, issue_native_participant_jwt

_MAX_EARLY_JOIN_SECONDS = 15 * 60
_MAX_LATE_JOIN_SECONDS = 15 * 60
_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_MEETING_NUMBER = re.compile(r"^[0-9]{9,13}$")


class JoinDenied(PermissionError):
    """Authorization failed. The message intentionally reveals no meeting data."""

    def __init__(self) -> None:
        super().__init__("This faculty member is not authorized for the requested meeting.")


@dataclass(frozen=True)
class AuthenticatedFaculty:
    """Identity verified by server-side auth middleware, NOT client-supplied claims."""

    faculty_id: str
    display_name: str
    is_active: bool


@dataclass(frozen=True)
class AssignedSandboxMeeting:
    """Server-owned immutable assignment and sandbox-only meeting metadata."""

    session_id: str
    faculty_id: str
    meeting_number: str
    meeting_passcode: str
    environment: str
    join_enabled: bool
    starts_at_epoch: int
    ends_at_epoch: int


@dataclass(frozen=True)
class AuthorizedIPadJoinTicket:
    """Sensitive, ephemeral payload returned only to the authenticated iPad."""

    meeting_number: str
    meeting_passcode: str
    display_name: str
    meeting_sdk_jwt: str
    expires_at_epoch: int

    def as_response(self) -> dict:
        """Exact field names expected by the staged Swift join adapter."""
        return {
            "meetingNumber": self.meeting_number,
            "meetingPasscode": self.meeting_passcode,
            "displayName": self.display_name,
            "meetingSDKJWT": self.meeting_sdk_jwt,
            "expiresAtEpoch": self.expires_at_epoch,
        }


class SandboxIPadJoinService:
    """Issue only a participant ticket for an eligible assigned Basic session.

    assignment_lookup is a trusted, server-owned, faculty assignment repository,
    keyed by the internal DocTutorials session ID. It must not be backed by
    arbitrary request JSON. No database, API server, or auth middleware is
    configured in this module; callers must supply real authenticated identity.
    """

    def __init__(
        self,
        assignment_lookup: Callable[[str], AssignedSandboxMeeting | None],
        signing_credentials: MeetingSDKSigningCredentials,
        *,
        clock: Callable[[], int] = lambda: int(time.time()),
    ) -> None:
        if not callable(assignment_lookup) or not callable(clock):
            raise TypeError("Trusted assignment lookup and clock are required.")
        if not isinstance(signing_credentials, MeetingSDKSigningCredentials):
            raise TypeError("Backend-only Meeting SDK credentials are required.")
        self._lookup = assignment_lookup
        self._credentials = signing_credentials
        self._clock = clock

    def issue_ticket(self, faculty: AuthenticatedFaculty, session_id: str) -> AuthorizedIPadJoinTicket:
        """Call only after the faculty request has been authenticated upstream.

        Avoid revealing whether a requested session exists or who teaches it.
        This does NOT grant a Zoom host role or bypass Zoom waiting rooms,
        meeting passcodes, guest authentication settings, or meeting security.
        """
        if (
            not isinstance(faculty, AuthenticatedFaculty)
            or faculty.is_active is not True
            or not isinstance(faculty.faculty_id, str)
            or not faculty.faculty_id
            or not isinstance(faculty.display_name, str)
            or not (1 <= len(faculty.display_name.strip()) <= 100)
            or any(ord(c) < 32 for c in faculty.display_name)
            or not isinstance(session_id, str)
            or _SESSION_ID.fullmatch(session_id) is None
        ):
            raise JoinDenied()

        assignment = self._lookup(session_id)
        if (
            not isinstance(assignment, AssignedSandboxMeeting)
            or assignment.session_id != session_id
            or assignment.faculty_id != faculty.faculty_id
            or assignment.environment != "zoom_basic_sandbox"
            or assignment.join_enabled is not True
            or not isinstance(assignment.meeting_number, str)
            or _MEETING_NUMBER.fullmatch(assignment.meeting_number) is None
            or not isinstance(assignment.meeting_passcode, str)
            or len(assignment.meeting_passcode) > 64
            or type(assignment.starts_at_epoch) is not int
            or type(assignment.ends_at_epoch) is not int
            or assignment.starts_at_epoch >= assignment.ends_at_epoch
        ):
            raise JoinDenied()

        now = self._clock()
        if (
            type(now) is not int
            or now < assignment.starts_at_epoch - _MAX_EARLY_JOIN_SECONDS
            or now >= assignment.ends_at_epoch + _MAX_LATE_JOIN_SECONDS
        ):
            raise JoinDenied()

        # SDK requires at least a 30-minute token lifetime. Issuing this
        # ticket is authorized by faculty/session policy at the time of issue;
        # the SDK JWT is not a substitute for Zoom's meeting access controls.
        jwt = issue_native_participant_jwt(
            self._credentials, assignment.meeting_number, now=now
        )
        return AuthorizedIPadJoinTicket(
            meeting_number=assignment.meeting_number,
            meeting_passcode=assignment.meeting_passcode,
            display_name=faculty.display_name.strip(),
            meeting_sdk_jwt=jwt,
            expires_at_epoch=now + 1_800,
        )
