"""Offline, no credentials/network: faculty-to-meeting authorization tests."""
import base64
import json
import unittest
from dataclasses import replace

from backend.ipad_join_authorization import (
    AssignedSandboxMeeting,
    AuthenticatedFaculty,
    JoinDenied,
    SandboxIPadJoinService,
)
from backend.ipad_sdk_jwt import MeetingSDKSigningCredentials


def decode_payload(jwt):
    segment = jwt.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


class SandboxIPadJoinServiceTests(unittest.TestCase):
    NOW = 1_800_000_000

    def setUp(self):
        self.faculty = AuthenticatedFaculty("faculty-001", "Faculty Demo", True)
        self.session = AssignedSandboxMeeting(
            session_id="sandbox-session",
            faculty_id="faculty-001",
            meeting_number="12345678901",
            meeting_passcode="test-only-passcode",
            environment="zoom_basic_sandbox",
            join_enabled=True,
            starts_at_epoch=self.NOW - 120,
            ends_at_epoch=self.NOW + 3600,
        )
        self.service = SandboxIPadJoinService(
            assignment_lookup=lambda session_id: self.session if session_id == "sandbox-session" else None,
            signing_credentials=MeetingSDKSigningCredentials(
                "fake-sdk-client-id", "fake-unit-test-secret"
            ),
            clock=lambda: self.NOW,
        )

    def test_authorized_faculty_receives_only_non_host_ticket(self):
        ticket = self.service.issue_ticket(self.faculty, "sandbox-session")
        response = ticket.as_response()
        self.assertEqual(response["meetingNumber"], self.session.meeting_number)
        self.assertEqual(response["meetingPasscode"], self.session.meeting_passcode)
        self.assertEqual(response["displayName"], self.faculty.display_name)
        self.assertEqual(response["expiresAtEpoch"], self.NOW + 1800)
        claims = decode_payload(response["meetingSDKJWT"])
        self.assertEqual(claims["role"], 0)
        self.assertEqual(claims["mn"], self.session.meeting_number)
        self.assertNotIn("clientSecret", response)
        self.assertNotIn("hostPassword", response)

    def test_other_faculty_cannot_join(self):
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(replace(self.faculty, faculty_id="faculty-002"), "sandbox-session")

    def test_inactive_faculty_cannot_join(self):
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(replace(self.faculty, is_active=False), "sandbox-session")

    def test_missing_session_denied_without_leak(self):
        with self.assertRaises(JoinDenied) as result:
            self.service.issue_ticket(self.faculty, "unknown-session")
        self.assertNotIn("unknown-session", str(result.exception))

    def test_untrusted_session_id_denied_before_lookup(self):
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(self.faculty, "../sandbox-session")

    def test_production_or_other_account_never_authorized(self):
        for environment in ("production", "paid_staging", "zoom_webinar", ""):
            with self.subTest(environment=environment):
                self.session = replace(self.session, environment=environment)
                with self.assertRaises(JoinDenied):
                    self.service.issue_ticket(self.faculty, "sandbox-session")

    def test_disabled_session_denied(self):
        self.session = replace(self.session, join_enabled=False)
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(self.faculty, "sandbox-session")

    def test_too_early_denied(self):
        self.session = replace(self.session, starts_at_epoch=self.NOW + 901)
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(self.faculty, "sandbox-session")

    def test_too_late_denied(self):
        self.session = replace(self.session, ends_at_epoch=self.NOW - 900)
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(self.faculty, "sandbox-session")

    def test_invalid_session_time_or_meeting_number_denied(self):
        for changes in (
            {"meeting_number": "NOT-ZOOM"},
            {"meeting_number": "12345"},
            {"starts_at_epoch": self.NOW + 100, "ends_at_epoch": self.NOW - 100},
            {"meeting_passcode": "x" * 65},
        ):
            with self.subTest(changes=changes):
                base = self.session
                self.session = replace(base, **changes)
                with self.assertRaises(JoinDenied):
                    self.service.issue_ticket(self.faculty, "sandbox-session")
                self.session = base

    def test_assignment_session_id_mismatch_denied(self):
        self.session = replace(self.session, session_id="different-session")
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(self.faculty, "sandbox-session")

    def test_no_identity_is_not_authorized(self):
        with self.assertRaises(JoinDenied):
            self.service.issue_ticket(None, "sandbox-session")


if __name__ == "__main__":
    unittest.main()
