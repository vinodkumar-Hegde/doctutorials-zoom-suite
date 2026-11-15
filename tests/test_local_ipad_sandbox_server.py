"""Offline local HTTPS sandbox launcher tests; no real SDK keys, Zoom calls or listeners."""
from __future__ import annotations

import json
import stat
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.faculty_password_auth import SandboxFacultyPasswordRecord, hash_static_password
from backend.ipad_join_authorization import AssignedSandboxMeeting
from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials
from backend.local_ipad_sandbox_server import (
    create_local_sandbox_app, read_private_sandbox_assignment, save_private_sandbox_assignment,
)

_NOW = 1_800_000_000
_PASSWORD = "not-a-real-password-for-offline-test-only"


class LocalIPadSandboxServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_static_password(_PASSWORD)

    def setUp(self):
        self.faculty = SandboxFacultyPasswordRecord(
            "sandbox-faculty", "Sandbox Faculty", self.password_hash
        )
        self.assignment = AssignedSandboxMeeting(
            "ipad-sandbox-class", "sandbox-faculty", "12345678901", "fake-passcode",
            "zoom_basic_sandbox", True, _NOW - 60, _NOW + 3600,
        )
        self.credentials = MeetingSDKSigningCredentials("fake-sdk-app-id", "fake-sdk-app-secret")

    def test_local_login_then_join_ticket_uses_same_verified_faculty(self):
        app = create_local_sandbox_app(
            self.faculty, self.assignment, self.credentials, clock=lambda: _NOW
        )
        client = TestClient(app, base_url="https://localhost")
        login = client.post("/api/faculty/login", json={
            "facultyId": "sandbox-faculty", "password": _PASSWORD,
        })
        self.assertEqual(login.status_code, 200)
        token = login.json()["accessToken"]
        join = client.post("/api/sessions/ipad-sandbox-class/join/ipad",
                           headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(join.status_code, 200)
        self.assertEqual(join.json()["meetingNumber"], "12345678901")
        self.assertNotIn(_PASSWORD, join.text)
        self.assertNotIn("fake-sdk-app-secret", join.text)

    def test_no_bearer_token_denied_for_join(self):
        app = create_local_sandbox_app(
            self.faculty, self.assignment, self.credentials, clock=lambda: _NOW
        )
        client = TestClient(app, base_url="https://localhost")
        self.assertEqual(client.post("/api/sessions/ipad-sandbox-class/join/ipad").status_code, 401)

    def test_private_assignment_creation_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            save_private_sandbox_assignment(
                path, session_id=self.assignment.session_id,
                faculty_id=self.assignment.faculty_id,
                meeting_number=self.assignment.meeting_number,
                meeting_passcode=self.assignment.meeting_passcode,
                starts_at_epoch=self.assignment.starts_at_epoch,
                ends_at_epoch=self.assignment.ends_at_epoch,
            )
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(read_private_sandbox_assignment(path), self.assignment)
            with self.assertRaises(FileExistsError):
                save_private_sandbox_assignment(
                    path, session_id="another", faculty_id="sandbox-faculty",
                    meeting_number="12345678901", meeting_passcode="",
                    starts_at_epoch=_NOW, ends_at_epoch=_NOW + 300,
                )

    def test_assignment_rejects_world_readable_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            save_private_sandbox_assignment(
                path, session_id="ipad-sandbox-class", faculty_id="sandbox-faculty",
                meeting_number="12345678901", meeting_passcode="abc",
                starts_at_epoch=_NOW, ends_at_epoch=_NOW + 300,
            )
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                read_private_sandbox_assignment(path)

    def test_invalid_sandbox_assignment_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.json"
            path.write_text(json.dumps({
                "sessionId": "ipad-sandbox-class", "facultyId": "sandbox-faculty",
                "meetingNumber": "12345678901", "meetingPasscode": "",
                "environment": "production", "joinEnabled": True,
                "startsAtEpoch": _NOW, "endsAtEpoch": _NOW + 300,
            }))
            path.chmod(0o600)
            with self.assertRaises(ValueError):
                read_private_sandbox_assignment(path)

    def test_cross_faculty_assignment_cannot_start(self):
        assigned = AssignedSandboxMeeting(
            "ipad-sandbox-class", "another-faculty", "12345678901", "",
            "zoom_basic_sandbox", True, _NOW - 10, _NOW + 300,
        )
        with self.assertRaises(ValueError):
            create_local_sandbox_app(
                self.faculty, assigned, self.credentials, clock=lambda: _NOW
            )


if __name__ == "__main__":
    unittest.main()
