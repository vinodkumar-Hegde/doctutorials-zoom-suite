"""Offline first-party static-password and HTTPS join API integration tests.

No real passwords, SDK client secrets, faculty data, Zoom calls or network.
Run after installing backend/requirements-ipad-dev.txt:
python3 -m unittest discover -s tests -p 'test_faculty_password_auth.py' -v
"""
from __future__ import annotations

import json
import stat
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from backend.faculty_password_auth import (
    SandboxFacultyPasswordRecord,
    StaticFacultyPasswordAuthenticator,
    hash_static_password,
)
from backend.faculty_password_http import create_first_party_faculty_app
from backend.ipad_join_authorization import AssignedSandboxMeeting, SandboxIPadJoinService
from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials

_NOW = 1_800_000_000
_FACULTY = "sandbox-faculty"
_PASSWORD = "only-for-unit-tests-not-a-real-password-42"


class FacultyPasswordAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.password_hash = hash_static_password(_PASSWORD)

    def setUp(self) -> None:
        self.now = _NOW
        self.record = SandboxFacultyPasswordRecord(
            _FACULTY, "Demo Faculty", self.password_hash
        )
        self.auth = StaticFacultyPasswordAuthenticator(
            self.record, clock=lambda: self.now
        )

    def test_correct_password_yields_short_lived_opaque_token(self):
        result = self.auth.authenticate(_FACULTY, _PASSWORD)
        self.assertIsNotNone(result)
        token, expires = result
        self.assertGreaterEqual(len(token), 40)
        self.assertEqual(expires, self.now + 900)
        principal = self.auth.verify_faculty_token(token)
        self.assertEqual(principal.faculty_id, _FACULTY)
        self.assertEqual(principal.display_name, "Demo Faculty")

    def test_static_password_does_not_mean_static_session_token(self):
        first = self.auth.authenticate(_FACULTY, _PASSWORD)[0]
        second = self.auth.authenticate(_FACULTY, _PASSWORD)[0]
        self.assertNotEqual(first, second)

    def test_wrong_password_denied(self):
        self.assertIsNone(self.auth.authenticate(_FACULTY, "incorrect-password-long-enough"))
        self.assertIsNone(self.auth.verify_faculty_token("z" * 43))

    def test_wrong_faculty_denied(self):
        self.assertIsNone(self.auth.authenticate("another-faculty", _PASSWORD))

    def test_inactive_faculty_denied(self):
        auth = StaticFacultyPasswordAuthenticator(
            replace(self.record, is_active=False),
            clock=lambda: self.now,
        )
        self.assertIsNone(auth.authenticate(_FACULTY, _PASSWORD))

    def test_session_expires(self):
        token = self.auth.authenticate(_FACULTY, _PASSWORD)[0]
        self.now += 900
        self.assertIsNone(self.auth.verify_faculty_token(token))

    def test_logout_revokes_session(self):
        token = self.auth.authenticate(_FACULTY, _PASSWORD)[0]
        self.auth.revoke_token(token)
        self.assertIsNone(self.auth.verify_faculty_token(token))

    def test_five_bad_passwords_lock_account_for_fifteen_minutes(self):
        for i in range(5):
            self.assertIsNone(self.auth.authenticate(_FACULTY, "incorrect-password-long-enough"))
        self.assertIsNone(self.auth.authenticate(_FACULTY, _PASSWORD))
        self.now += 900
        self.assertIsNotNone(self.auth.authenticate(_FACULTY, _PASSWORD))

    def test_hash_has_salt_and_never_contains_plaintext(self):
        other = hash_static_password(_PASSWORD)
        self.assertNotEqual(other, self.password_hash)
        self.assertEqual(self.password_hash.split(":")[0], "scrypt-v1")
        self.assertNotIn(_PASSWORD, other)

    def test_rejects_short_password(self):
        with self.assertRaises(ValueError):
            hash_static_password("short")

    def test_corrupt_hash_fails_closed(self):
        with self.assertRaises(ValueError):
            SandboxFacultyPasswordRecord(_FACULTY, "Demo Faculty", "sha256:unsafe")

    def test_private_config_file_mode_and_no_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "sandbox" / "faculty.json"
            self.record.save_new_private_file(dest)
            self.assertEqual(stat.S_IMODE(dest.stat().st_mode), 0o600)
            content = dest.read_text()
            self.assertNotIn(_PASSWORD, content)
            loaded = SandboxFacultyPasswordRecord.from_private_file(dest)
            self.assertEqual(loaded, self.record)
            with self.assertRaises(FileExistsError):
                self.record.save_new_private_file(dest)

    def test_rejects_world_readable_private_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "faculty.json"
            self.record.save_new_private_file(dest)
            dest.chmod(0o644)
            with self.assertRaises(ValueError):
                SandboxFacultyPasswordRecord.from_private_file(dest)

    def test_restart_invalidates_ephemeral_sessions(self):
        token = self.auth.authenticate(_FACULTY, _PASSWORD)[0]
        new_authenticator = StaticFacultyPasswordAuthenticator(self.record, clock=lambda: self.now)
        self.assertIsNone(new_authenticator.verify_faculty_token(token))


class FacultyPasswordHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.password_hash = hash_static_password(_PASSWORD)

    def setUp(self):
        self.now = _NOW
        record = SandboxFacultyPasswordRecord(_FACULTY, "Demo Faculty", self.password_hash)
        self.auth = StaticFacultyPasswordAuthenticator(record, clock=lambda: self.now)
        assigned = AssignedSandboxMeeting(
            session_id="session-demo",
            faculty_id=_FACULTY,
            meeting_number="12345678901",
            meeting_passcode="not-a-real-passcode",
            environment="zoom_basic_sandbox",
            join_enabled=True,
            starts_at_epoch=_NOW - 10,
            ends_at_epoch=_NOW + 3600,
        )
        self.join = SandboxIPadJoinService(
            assignment_lookup=lambda session_id: assigned if session_id == "session-demo" else None,
            signing_credentials=MeetingSDKSigningCredentials("fake-id", "fake-secret"),
            clock=lambda: self.now,
        )
        self.make_app = lambda login=True, join=True: create_first_party_faculty_app(
            self.auth,
            self.join,
            enable_password_login_api=login,
            enable_ipad_join_api=join,
            allowed_hosts=("testserver",),
        )
        self.client = TestClient(self.make_app(), base_url="https://testserver")

    def login(self, *, password=_PASSWORD, faculty_id=_FACULTY, **kwargs):
        return self.client.post(
            "/api/faculty/login",
            json={"facultyId": faculty_id, "password": password},
            **kwargs,
        )

    def test_successful_login_then_participant_join_ticket(self):
        login = self.login()
        self.assertEqual(login.status_code, 200)
        self.assertEqual(set(login.json()), {"accessToken", "tokenType", "expiresAtEpoch"})
        self.assertEqual(login.json()["expiresAtEpoch"], self.now + 900)
        token = login.json()["accessToken"]
        response = self.client.post(
            "/api/sessions/session-demo/join/ipad",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["meetingNumber"], "12345678901")
        self.assertIn("meetingSDKJWT", response.json())

    def test_default_off_login_and_join(self):
        client = TestClient(self.make_app(login=False, join=False), base_url="https://testserver")
        response = client.post(
            "/api/faculty/login",
            json={"facultyId": _FACULTY, "password": _PASSWORD},
        )
        self.assertEqual(response.status_code, 503)
        join = client.post("/api/sessions/session-demo/join/ipad")
        self.assertEqual(join.status_code, 503)

    def test_wrong_password_returns_generic_denial(self):
        response = self.login(password="incorrect-password-long-enough")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(_FACULTY, response.text)
        self.assertNotIn("meetingSDKJWT", response.text)

    def test_missing_account_returns_generic_denial(self):
        response = self.login(faculty_id="unknown-user")
        self.assertEqual(response.status_code, 401)

    def test_insecure_http_denied_even_if_forwarded_header_claims_https(self):
        client = TestClient(self.make_app(), base_url="http://testserver")
        result = client.post(
            "/api/faculty/login",
            headers={"X-Forwarded-Proto": "https"},
            json={"facultyId": _FACULTY, "password": _PASSWORD},
        )
        self.assertEqual(result.status_code, 426)

    def test_untrusted_hostname_denied(self):
        client = TestClient(self.make_app(), base_url="https://untrusted.example")
        result = client.post(
            "/api/faculty/login",
            json={"facultyId": _FACULTY, "password": _PASSWORD},
        )
        self.assertEqual(result.status_code, 400)

    def test_password_or_token_not_leaked_in_response(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(_PASSWORD, response.text)
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertEqual(response.headers["pragma"], "no-cache")

    def test_login_request_rejects_extra_fields(self):
        payload = {"facultyId": _FACULTY, "password": _PASSWORD, "meetingNumber": "12345678901"}
        response = self.client.post("/api/faculty/login", json=payload)
        self.assertEqual(response.status_code, 400)

    def test_login_request_rejects_oversized_body(self):
        response = self.client.post(
            "/api/faculty/login",
            content=json.dumps({
                "facultyId": _FACULTY, "password": "x" * 5000,
            }),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)

    def test_login_requires_json_content_type(self):
        response = self.client.post(
            "/api/faculty/login",
            content="just a password",
            headers={"Content-Type": "text/plain"},
        )
        self.assertEqual(response.status_code, 415)

    def test_logout_revokes_token(self):
        token = self.login().json()["accessToken"]
        logout = self.client.post(
            "/api/faculty/logout", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(logout.status_code, 204)
        response = self.client.post(
            "/api/sessions/session-demo/join/ipad",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_token_cannot_join(self):
        token = self.login().json()["accessToken"]
        self.now += 900
        response = self.client.post(
            "/api/sessions/session-demo/join/ipad",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_can_be_enabled_without_zoom_join(self):
        client = TestClient(self.make_app(login=True, join=False), base_url="https://testserver")
        login = client.post("/api/faculty/login", json={
            "facultyId": _FACULTY, "password": _PASSWORD,
        })
        self.assertEqual(login.status_code, 200)
        join = client.post(
            "/api/sessions/session-demo/join/ipad",
            headers={"Authorization": "Bearer " + login.json()["accessToken"]},
        )
        self.assertEqual(join.status_code, 503)

    def test_http_password_login_is_not_publicly_registered(self):
        self.assertEqual(self.client.get("/docs").status_code, 404)
        self.assertEqual(self.client.get("/openapi.json").status_code, 404)
        self.assertEqual(self.client.get("/api/faculty/login").status_code, 405)


if __name__ == "__main__":
    unittest.main()
