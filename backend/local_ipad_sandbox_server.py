"""Local HTTPS Zoom Basic sandbox bootstrap: private assignment + first-party login.

Runs only on the Mac's LOOPBACK interface. No cloud or production exposure.
It is an intentionally single-faculty, single-sandbox-meeting pilot, NOT a
production authentication deployment. Use trusted local TLS certificates.
No credential values are printed or stored in Git.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.faculty_password_auth import (
    DEFAULT_CONFIG,
    SandboxFacultyPasswordRecord,
    StaticFacultyPasswordAuthenticator,
)
from backend.faculty_password_http import create_first_party_faculty_app
from backend.ipad_join_authorization import AssignedSandboxMeeting, SandboxIPadJoinService
from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials

DEFAULT_ASSIGNMENT = Path.home() / ".config" / "doctutorials" / "ipad-basic-assignment.json"
_SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_MEETING_RE = re.compile(r"^[0-9]{9,13}$")


def save_private_sandbox_assignment(
    destination: Path,
    *,
    session_id: str,
    faculty_id: str,
    meeting_number: str,
    meeting_passcode: str,
    starts_at_epoch: int,
    ends_at_epoch: int,
) -> None:
    """Create a private single-session sandbox assignment. No overwrite."""
    if (
        not isinstance(session_id, str) or _SESSION_RE.fullmatch(session_id) is None
        or not isinstance(faculty_id, str) or _SESSION_RE.fullmatch(faculty_id) is None
        or not isinstance(meeting_number, str) or _MEETING_RE.fullmatch(meeting_number) is None
        or not isinstance(meeting_passcode, str) or not (0 <= len(meeting_passcode) <= 64)
        or type(starts_at_epoch) is not int or type(ends_at_epoch) is not int
        or starts_at_epoch >= ends_at_epoch
    ):
        raise ValueError("Invalid private sandbox meeting assignment.")
    path = Path(destination).expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = json.dumps({
        "sessionId": session_id,
        "facultyId": faculty_id,
        "meetingNumber": meeting_number,
        "meetingPasscode": meeting_passcode,
        "environment": "zoom_basic_sandbox",
        "joinEnabled": True,
        "startsAtEpoch": starts_at_epoch,
        "endsAtEpoch": ends_at_epoch,
    }, separators=(",", ":")).encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def read_private_sandbox_assignment(path: Path) -> AssignedSandboxMeeting:
    source = Path(path).expanduser()
    if not source.is_file() or source.is_symlink():
        raise ValueError("Private sandbox meeting assignment is missing or unsafe.")
    if os.name == "posix" and (source.stat().st_mode & 0o077):
        raise ValueError("Private assignment must have mode 0600.")
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {
        "sessionId", "facultyId", "meetingNumber", "meetingPasscode",
        "environment", "joinEnabled", "startsAtEpoch", "endsAtEpoch",
    }:
        raise ValueError("Invalid private assignment format.")
    result = AssignedSandboxMeeting(
        session_id=data["sessionId"],
        faculty_id=data["facultyId"],
        meeting_number=data["meetingNumber"],
        meeting_passcode=data["meetingPasscode"],
        environment=data["environment"],
        join_enabled=data["joinEnabled"],
        starts_at_epoch=data["startsAtEpoch"],
        ends_at_epoch=data["endsAtEpoch"],
    )
    # Validate records BEFORE starting a web listener.
    if (
        _SESSION_RE.fullmatch(result.session_id) is None
        or _SESSION_RE.fullmatch(result.faculty_id) is None
        or _MEETING_RE.fullmatch(result.meeting_number) is None
        or result.environment != "zoom_basic_sandbox"
        or result.join_enabled is not True
        or not isinstance(result.meeting_passcode, str)
        or len(result.meeting_passcode) > 64
        or type(result.starts_at_epoch) is not int
        or type(result.ends_at_epoch) is not int
        or result.starts_at_epoch >= result.ends_at_epoch
    ):
        raise ValueError("Invalid or ineligible sandbox assignment.")
    return result


def create_local_sandbox_app(
    faculty_record: SandboxFacultyPasswordRecord,
    assigned: AssignedSandboxMeeting,
    credentials: MeetingSDKSigningCredentials,
    *,
    clock=None,
):
    """Compose the *actual* first-party login and authorization modules.

    This is callable by offline tests without hosting or secret disclosure.
    The network listener is configured only by main(), with TLS mandatory.
    """
    if faculty_record.faculty_id != assigned.faculty_id:
        raise ValueError("Assigned faculty must match the private sandbox login.")
    auth = StaticFacultyPasswordAuthenticator(
        faculty_record, **({"clock": clock} if clock is not None else {})
    )
    service = SandboxIPadJoinService(
        assignment_lookup=lambda session_id: (
            assigned if session_id == assigned.session_id else None
        ),
        signing_credentials=credentials,
        **({"clock": clock} if clock is not None else {}),
    )
    return create_first_party_faculty_app(
        auth,
        service,
        enable_password_login_api=True,
        enable_ipad_join_api=True,
        allowed_hosts=("localhost", "127.0.0.1"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Loopback-only HTTPS iPad sandbox pilot. Never publicly deploy.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    setup = subcommands.add_parser("setup-assignment", help="Save private Basic sandbox meeting metadata.")
    setup.add_argument("--session-id", default="ipad-sandbox-class")
    setup.add_argument("--faculty-id", default="sandbox-faculty")
    setup.add_argument("--output", type=Path, default=DEFAULT_ASSIGNMENT)
    start = subcommands.add_parser("serve-https", help="Start LOCALHOST TLS-only, no remote connections.")
    start.add_argument("--faculty-file", type=Path, default=DEFAULT_CONFIG)
    start.add_argument("--assignment-file", type=Path, default=DEFAULT_ASSIGNMENT)
    start.add_argument("--tls-cert", type=Path, required=True)
    start.add_argument("--tls-key", type=Path, required=True)
    start.add_argument("--port", type=int, default=8443)
    args = parser.parse_args()

    if args.command == "setup-assignment":
        # Required meeting number and passcode are provided privately in
        # Terminal, never typed into the source code or shell history.
        # Zoom commonly displays grouped IDs (e.g. "123 4567 8901").
        # A meeting number is not a secret; accept pasted spacing/hyphens.
        meeting_number = re.sub(r"[\s-]+", "", input("Zoom Basic sandbox Meeting number: ").strip())
        meeting_passcode = getpass.getpass("Zoom Basic sandbox meeting PASSCODE (hidden): ")
        now = int(time.time())
        try:
            save_private_sandbox_assignment(
                args.output,
                session_id=args.session_id,
                faculty_id=args.faculty_id,
                meeting_number=meeting_number,
                meeting_passcode=meeting_passcode,
                starts_at_epoch=now - 600,
                ends_at_epoch=now + 3600,
            )
        except (ValueError, FileExistsError) as exc:
            raise SystemExit(f"Assignment setup incomplete: {exc}") from None
        print("Private Basic sandbox assignment saved outside GitHub.")
        print(f"Assigned DocTutorials session ID: {args.session_id}")
        print("Window: now through approximately the next hour; regenerate when expired.")
        print("Meeting details/passcode were NOT printed. No server was started.")
        return

    cert = args.tls_cert.expanduser()
    key = args.tls_key.expanduser()
    if not cert.is_file() or not key.is_file() or args.port < 1024 or args.port > 65535:
        raise SystemExit("Specify existing local TLS certificate/key and an unprivileged port.")
    if key.is_symlink() or (os.name == "posix" and key.stat().st_mode & 0o077):
        raise SystemExit("The private TLS key must be a regular, mode-0600 protected file.")

    faculty = SandboxFacultyPasswordRecord.from_private_file(args.faculty_file)
    assigned = read_private_sandbox_assignment(args.assignment_file)
    if assigned.environment != "zoom_basic_sandbox":
        raise SystemExit("Only the free Basic sandbox is permitted.")
    client_id = getpass.getpass("Meeting SDK General App Client ID (hidden): ").strip()
    client_secret = getpass.getpass("Meeting SDK General App Client Secret (hidden): ").strip()
    try:
        credentials = MeetingSDKSigningCredentials(client_id, client_secret)
    except ValueError as exc:
        raise SystemExit("Zoom Meeting SDK sandbox credentials were not configured.") from None

    app = create_local_sandbox_app(faculty, assigned, credentials)

    import uvicorn
    print(f"Local HTTPS-only faculty + join API: https://localhost:{args.port}")
    print("Bound to 127.0.0.1 ONLY; not reachable from other machines/iPads.")
    print("SSL certificate must be trusted by the iPad Simulator to connect.")
    print("Stop with Ctrl+C. No SDK secret/token is printed.")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        ssl_certfile=str(cert),
        ssl_keyfile=str(key),
        access_log=False,
        log_level="warning",
        proxy_headers=False,
        workers=1,
    )


if __name__ == "__main__":
    main()
