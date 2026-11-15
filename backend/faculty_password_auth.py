"""First-party, ONE-faculty static-password auth for the Zoom Basic sandbox.

No Firebase, Google, Microsoft or other authentication provider is used.
This intentionally supports ONE operator-created sandbox faculty principal,
NOT a production multi-faculty identity database.

Passwords are salted+hashed with scrypt and NEVER committed or put into the
iPad app. Successful login returns a short-lived opaque random access token,
whose SHA-256 digest alone is held in server memory. Sessions expire after
15 minutes and are lost on restart. Server/host must enforce HTTPS.

Create the fixed password locally via:
    python3 -m backend.faculty_password_auth setup --faculty-id sandbox-faculty --display-name "Sandbox Faculty"
The CLI prompts without echoing the password and writes a private JSON file
outside this repository. Do not provide passwords as command line flags.
"""
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from backend.ipad_join_authorization import AuthenticatedFaculty

# OWASP scrypt fallback recommendation: N=2^17, r=8, p=1 (~128 MiB).
_SCRYPT_N = 1 << 17
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_MEM_LIMIT = 256 * 1024 * 1024
_SALT_BYTES = 16
_HASH_BYTES = 32
_HASH_PREFIX = "scrypt-v1"
_FACULTY_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_-]{40,64}$")
_SESSION_SECONDS = 15 * 60
_MAX_SESSIONS = 32
_MAX_FAILURES = 5
_FAILURE_WINDOW_SECONDS = 15 * 60
_LOCKOUT_SECONDS = 15 * 60
DEFAULT_CONFIG = Path.home() / ".config" / "doctutorials" / "faculty-basic-sandbox.json"


def _password_is_valid(password: object) -> bool:
    return (
        isinstance(password, str)
        and 16 <= len(password) <= 128
        and "\x00" not in password
        and "\n" not in password
        and "\r" not in password
    )


def hash_static_password(password: str, *, salt: bytes | None = None) -> str:
    """One-way hash, safe to place in a private server configuration file."""
    if not _password_is_valid(password):
        raise ValueError("A static faculty password must be 16-128 characters.")
    if salt is None:
        salt = secrets.token_bytes(_SALT_BYTES)
    if not isinstance(salt, bytes) or len(salt) != _SALT_BYTES:
        raise ValueError("A random 16-byte salt is required.")
    value = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        maxmem=_SCRYPT_MEM_LIMIT,
        dklen=_HASH_BYTES,
    )
    return ":".join(
        (_HASH_PREFIX, base64.b64encode(salt).decode("ascii"), base64.b64encode(value).decode("ascii"))
    )


def _decode_hash(password_hash: str) -> tuple[bytes, bytes]:
    if not isinstance(password_hash, str):
        raise ValueError("Invalid faculty password configuration.")
    pieces = password_hash.split(":")
    if len(pieces) != 3 or pieces[0] != _HASH_PREFIX:
        raise ValueError("Unsupported password hash configuration.")
    try:
        salt = base64.b64decode(pieces[1], validate=True)
        expected = base64.b64decode(pieces[2], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid faculty password hash encoding.") from exc
    if len(salt) != _SALT_BYTES or len(expected) != _HASH_BYTES:
        raise ValueError("Invalid faculty password hash length.")
    return salt, expected


@dataclass(frozen=True)
class SandboxFacultyPasswordRecord:
    faculty_id: str
    display_name: str
    password_hash: str
    is_active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.faculty_id, str) or _FACULTY_ID.fullmatch(self.faculty_id) is None:
            raise ValueError("Invalid sandbox faculty ID.")
        if (
            not isinstance(self.display_name, str)
            or not (1 <= len(self.display_name.strip()) <= 100)
            or any(ord(c) < 32 for c in self.display_name)
        ):
            raise ValueError("Invalid faculty display name.")
        if type(self.is_active) is not bool:
            raise ValueError("Invalid faculty activation flag.")
        _decode_hash(self.password_hash)

    def save_new_private_file(self, destination: Path) -> None:
        """Write a PRIVATE hash-only config; refuse clobbers/symlinks."""
        path = Path(destination).expanduser()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "facultyId": self.faculty_id,
                "displayName": self.display_name,
                "passwordHash": self.password_hash,
                "isActive": self.is_active,
            },
            indent=2,
        ).encode("utf-8")
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
        except BaseException:
            path.unlink(missing_ok=True)
            raise

    @classmethod
    def from_private_file(cls, path: Path) -> "SandboxFacultyPasswordRecord":
        source = Path(path).expanduser()
        if not source.is_file() or source.is_symlink():
            raise ValueError("Sandbox faculty password file is missing or unsafe.")
        if os.name == "posix" and (source.stat().st_mode & 0o077):
            raise ValueError("Sandbox faculty file must not be group/world-readable.")
        with source.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or set(data) != {"facultyId", "displayName", "passwordHash", "isActive"}:
            raise ValueError("Invalid sandbox faculty password file.")
        return cls(
            faculty_id=data["facultyId"],
            display_name=data["displayName"],
            password_hash=data["passwordHash"],
            is_active=data["isActive"],
        )


class StaticFacultyPasswordAuthenticator:
    """An in-process first-party password verifier for a single sandbox faculty.

    A static password verifies once, yielding a **different** 15-minute bearer
    token each login. Only token digests are held in memory. Restart invalidates
    all sessions. Only one instance/worker is supported in the Basic sandbox;
    multi-instance deployments need a shared session/revocation store.
    """

    def __init__(
        self,
        record: SandboxFacultyPasswordRecord,
        *,
        clock: Callable[[], int] = lambda: int(time.time()),
    ) -> None:
        if not isinstance(record, SandboxFacultyPasswordRecord) or not callable(clock):
            raise TypeError("A trusted sandbox faculty record and clock are required.")
        self._faculty = record
        self._clock = clock
        self._salt, self._password_digest = _decode_hash(record.password_hash)
        self._lock = threading.RLock()
        self._sessions: dict[bytes, int] = {}
        self._failures: deque[int] = deque()
        self._locked_until = 0

    def _verify_password(self, candidate: str) -> bool:
        digest = hashlib.scrypt(
            candidate.encode("utf-8"),
            salt=self._salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            maxmem=_SCRYPT_MEM_LIMIT,
            dklen=_HASH_BYTES,
        )
        return hmac.compare_digest(digest, self._password_digest)

    def authenticate(self, faculty_id: str, password: str) -> tuple[str, int] | None:
        """Generic failure for incorrect identity, password, inactivity or lock."""
        if (
            not isinstance(faculty_id, str)
            or _FACULTY_ID.fullmatch(faculty_id) is None
            or not _password_is_valid(password)
        ):
            return None
        with self._lock:
            now = self._clock()
            if self._locked_until > now:
                return None
            while self._failures and self._failures[0] <= now - _FAILURE_WINDOW_SECONDS:
                self._failures.popleft()

            valid = self._verify_password(password)
            if not valid or faculty_id != self._faculty.faculty_id or not self._faculty.is_active:
                self._failures.append(now)
                if len(self._failures) >= _MAX_FAILURES:
                    self._locked_until = now + _LOCKOUT_SECONDS
                    self._failures.clear()
                return None

            self._failures.clear()
            self._locked_until = 0
            for digest, exp in list(self._sessions.items()):
                if exp <= now:
                    del self._sessions[digest]
            if len(self._sessions) >= _MAX_SESSIONS:
                # Bound per-faculty concurrent sessions; explicit logout or
                # expiry required to create additional sessions.
                return None
            token = secrets.token_urlsafe(32)
            expiration = now + _SESSION_SECONDS
            self._sessions[hashlib.sha256(token.encode("ascii")).digest()] = expiration
            return token, expiration

    def verify_faculty_token(self, token: str) -> AuthenticatedFaculty | None:
        if not isinstance(token, str) or _TOKEN.fullmatch(token) is None:
            return None
        with self._lock:
            digest = hashlib.sha256(token.encode("ascii")).digest()
            exp = self._sessions.get(digest)
            if exp is None:
                return None
            now = self._clock()
            if not self._faculty.is_active or now >= exp:
                self._sessions.pop(digest, None)
                return None
            return AuthenticatedFaculty(self._faculty.faculty_id, self._faculty.display_name, True)

    def revoke_token(self, token: str) -> None:
        if not isinstance(token, str) or _TOKEN.fullmatch(token) is None:
            return
        with self._lock:
            self._sessions.pop(hashlib.sha256(token.encode("ascii")).digest(), None)


def main() -> None:
    parser = argparse.ArgumentParser(description="Set ONE private static password for Zoom Basic sandbox faculty.")
    subs = parser.add_subparsers(dest="command", required=True)
    setup = subs.add_parser("setup", help="Prompt securely and create a new local salted-hash config.")
    setup.add_argument("--faculty-id", default="sandbox-faculty")
    setup.add_argument("--display-name", default="Sandbox Faculty")
    setup.add_argument("--output", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    if args.command == "setup":
        first = getpass.getpass("Choose a static faculty password (16-128 characters; input hidden): ")
        second = getpass.getpass("Re-enter the password (input hidden): ")
        if not hmac.compare_digest(first, second):
            raise SystemExit("Passwords do not match. No file created.")
        try:
            record = SandboxFacultyPasswordRecord(
                args.faculty_id,
                args.display_name,
                hash_static_password(first),
            )
            record.save_new_private_file(args.output)
        except (ValueError, FileExistsError) as exc:
            raise SystemExit(f"Setup was not completed: {exc}") from None
        print(f"Created PRIVATE salted-password-hash config at: {Path(args.output).expanduser()}")
        print("Password remains fixed until you explicitly rotate it. Do NOT share it in chat or Git.")
        print("No Zoom or public backend service was started.")


if __name__ == "__main__":
    main()
