"""Meeting SDK JWT signing for a *trusted* DocTutorials backend only.

The signing Client Secret must come from the server's secret store. Never ship
it in the iPad app or use it as an existing Server-to-Server OAuth credential.
This module does not expose a public HTTP endpoint or authorize any faculty.

Callers MUST first authenticate the faculty member and check the assignment
for the requested Zoom Basic sandbox meeting. This signer is a last step,
not a faculty authorization policy.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

MIN_TOKEN_SECONDS = 1_800  # Zoom native SDK requires >=30 minutes.
MAX_TOKEN_SECONDS = 7_200  # Application policy: cap to two hours.


class MeetingSDKTokenConfigError(ValueError):
    """Raised for an invalid meeting or Meeting SDK signing configuration."""


@dataclass(frozen=True)
class MeetingSDKSigningCredentials:
    client_id: str
    client_secret: str

    def __post_init__(self) -> None:
        for value in (self.client_id, self.client_secret):
            if not isinstance(value, str) or not value or value.strip() != value:
                raise MeetingSDKTokenConfigError("Meeting SDK credentials are not configured.")


def _b64url(source: bytes) -> str:
    return base64.urlsafe_b64encode(source).rstrip(b"=").decode("ascii")


def issue_native_participant_jwt(
    credentials: MeetingSDKSigningCredentials,
    meeting_number: str,
    *,
    now: int | None = None,
    duration_seconds: int = MIN_TOKEN_SECONDS,
) -> str:
    """Return an HS256 JWT for the specified Meeting SDK *participant*.

    Zoom native Meeting SDK requires appKey, iat, exp and tokenExp. We also
    scope this issuance to a specific meeting number (mn) and role=0. SDK
    authorization is not a substitute for Zoom's own meeting entry rules.
    The returned token is sensitive: never print, persist or log it.
    """
    if not isinstance(credentials, MeetingSDKSigningCredentials):
        raise MeetingSDKTokenConfigError("Missing Meeting SDK signing credentials.")
    if not isinstance(meeting_number, str) or not meeting_number.isascii() or not meeting_number.isdigit() or not (9 <= len(meeting_number) <= 13):
        raise MeetingSDKTokenConfigError("Expected a numeric Zoom meeting number.")
    if type(duration_seconds) is not int or not (MIN_TOKEN_SECONDS <= duration_seconds <= MAX_TOKEN_SECONDS):
        raise MeetingSDKTokenConfigError("Unsupported SDK token lifetime.")
    if now is None:
        now = int(time.time())
    if type(now) is not int or now <= 0:
        raise MeetingSDKTokenConfigError("Invalid issuance timestamp.")

    header = {"alg": "HS256", "typ": "JWT"}
    expires_at = now + duration_seconds
    payload = {
        "appKey": credentials.client_id,
        "mn": meeting_number,
        "role": 0,  # Participant, never Zoom host.
        "iat": now,
        "exp": expires_at,
        "tokenExp": expires_at,
    }
    header_token = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_token = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    unsigned = f"{header_token}.{payload_token}"
    signature = hmac.new(credentials.client_secret.encode("utf-8"), unsigned.encode("ascii"), hashlib.sha256).digest()
    return f"{unsigned}.{_b64url(signature)}"
