"""Offline FastAPI contract tests: no Zoom calls, secrets or network.

Run with: python3 -m unittest discover -s tests -p 'test_ipad_join_http.py' -v
Requires backend/requirements-ipad-dev.txt (FastAPI + httpx).
"""
from __future__ import annotations

import base64
import json
import unittest
from dataclasses import replace

from fastapi.testclient import TestClient

from backend.ipad_join_authorization import (
    AssignedSandboxMeeting,
    AuthenticatedFaculty,
    SandboxIPadJoinService,
)
from backend.ipad_join_http import create_ipad_join_app
from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials

_NOW = 1_800_000_000
_ACCESS_TOKEN = "sandbox-unit-test-verified-bearer-token"
_TEST_SECRET = "not-real-never-a-zoom-client-secret"


def jwt_claims(token: str) -> dict:
    piece = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(piece + "=" * (-len(piece) % 4)))


class IPadJoinHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.faculty = AuthenticatedFaculty("faculty-001", "Test Faculty", True)
        self.assignment = AssignedSandboxMeeting(
            session_id="test-session",
            faculty_id=self.faculty.faculty_id,
            meeting_number="12345678901",
            meeting_passcode="sandbox-test-only-passcode",
            environment="zoom_basic_sandbox",
            join_enabled=True,
            starts_at_epoch=_NOW - 30,
            ends_at_epoch=_NOW + 3600,
        )
        self.lookup = lambda session_id: self.assignment if session_id == "test-session" else None
        self.verifier = lambda token: self.faculty if token == _ACCESS_TOKEN else None
        self.service = SandboxIPadJoinService(
            assignment_lookup=self.lookup,
            signing_credentials=MeetingSDKSigningCredentials("fake-client-id", _TEST_SECRET),
            clock=lambda: _NOW,
        )
        self.make_app = lambda enabled=True: create_ipad_join_app(
            self.service,
            self.verifier,
            enable_ipad_join_api=enabled,
            allowed_hosts=("testserver",),
        )
        self.client = TestClient(self.make_app(), base_url="https://testserver")

    @property
    def auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {_ACCESS_TOKEN}"}

    def post(self, session_id="test-session", **kwargs):
        return self.client.post(f"/api/sessions/{session_id}/join/ipad", **kwargs)

    def test_success_returns_participant_ticket_with_exact_fields(self):
        response = self.post(headers=self.auth)
        self.assertEqual(response.status_code, 200)
        ticket = response.json()
        self.assertEqual(set(ticket), {
            "meetingNumber", "meetingPasscode", "displayName",
            "meetingSDKJWT", "expiresAtEpoch",
        })
        self.assertEqual(ticket["meetingNumber"], "12345678901")
        self.assertEqual(ticket["displayName"], "Test Faculty")
        self.assertEqual(ticket["expiresAtEpoch"], _NOW + 1800)
        claims = jwt_claims(ticket["meetingSDKJWT"])
        self.assertEqual(claims["role"], 0)
        self.assertEqual(claims["mn"], ticket["meetingNumber"])
        self.assertNotIn(_TEST_SECRET, response.text)
        self.assertNotIn("hostPassword", response.text)

    def test_sensitive_ticket_is_not_cacheable(self):
        response = self.post(headers=self.auth)
        self.assertEqual(response.headers["cache-control"], "no-store, private")
        self.assertEqual(response.headers["pragma"], "no-cache")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_endpoint_disabled_by_default(self):
        client = TestClient(create_ipad_join_app(
            self.service, self.verifier, allowed_hosts=("testserver",)
        ), base_url="https://testserver")
        response = client.post("/api/sessions/test-session/join/ipad", headers=self.auth)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("meetingSDKJWT", response.text)

    def test_without_bearer_token_returns_401(self):
        response = self.post()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_wrong_token_returns_401(self):
        response = self.post(headers={"Authorization": "Bearer " + "z" * 40})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("meetingSDKJWT", response.text)

    def test_bearer_format_is_strict(self):
        for value in ("", "Basic " + _ACCESS_TOKEN, "Bearer short", "bearer " + _ACCESS_TOKEN):
            with self.subTest(value=value[:16]):
                response = self.post(headers={"Authorization": value})
                self.assertEqual(response.status_code, 401)

    def test_identity_verifier_exception_fails_closed(self):
        def broken_verifier(token):
            raise RuntimeError("not disclosed to client")
        app = create_ipad_join_app(
            self.service, broken_verifier,
            enable_ipad_join_api=True, allowed_hosts=("testserver",),
        )
        client = TestClient(app, base_url="https://testserver")
        response = client.post("/api/sessions/test-session/join/ipad", headers=self.auth)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("not disclosed", response.text)

    def test_other_faculty_is_denied(self):
        self.faculty = replace(self.faculty, faculty_id="faculty-002")
        response = self.post(headers=self.auth)
        self.assertEqual(response.status_code, 403)

    def test_inactive_faculty_is_denied(self):
        self.faculty = replace(self.faculty, is_active=False)
        response = self.post(headers=self.auth)
        self.assertEqual(response.status_code, 403)

    def test_unknown_session_denied_without_existence_leak(self):
        response = self.post("not-known", headers=self.auth)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("not-known", response.text)

    def test_non_sandbox_assignment_denied(self):
        self.assignment = replace(self.assignment, environment="production")
        response = self.post(headers=self.auth)
        self.assertEqual(response.status_code, 403)

    def test_body_cannot_supply_identity_or_meeting(self):
        response = self.post(
            headers=self.auth,
            json={"faculty_id": "faculty-001", "zoom_meeting_id": "12345678901"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("meetingSDKJWT", response.text)

    def test_insecure_http_denied_even_with_forwarded_https_header(self):
        client = TestClient(self.make_app(), base_url="http://testserver")
        headers = dict(self.auth)
        headers["X-Forwarded-Proto"] = "https"
        response = client.post("/api/sessions/test-session/join/ipad", headers=headers)
        self.assertEqual(response.status_code, 426)

    def test_untrusted_host_denied(self):
        client = TestClient(self.make_app(), base_url="https://evil.example")
        response = client.post("/api/sessions/test-session/join/ipad", headers=self.auth)
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("meetingSDKJWT", response.text)

    def test_get_cannot_issue_ticket(self):
        response = self.client.get("/api/sessions/test-session/join/ipad", headers=self.auth)
        self.assertEqual(response.status_code, 405)

    def test_docs_disabled(self):
        self.assertEqual(self.client.get("/docs").status_code, 404)
        self.assertEqual(self.client.get("/openapi.json").status_code, 404)

    def test_disallows_wildcard_host_even_when_disabled(self):
        with self.assertRaises(ValueError):
            create_ipad_join_app(self.service, self.verifier, allowed_hosts=("*",))

    def test_verifier_required_to_construct_app(self):
        with self.assertRaises(TypeError):
            create_ipad_join_app(self.service, None, allowed_hosts=("testserver",))

    def test_response_error_is_not_cacheable(self):
        response = self.post()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["cache-control"], "no-store, private")


if __name__ == "__main__":
    unittest.main()
