"""No network, credentials or Zoom API calls are required for these tests."""
import base64
import hashlib
import hmac
import json
import unittest

from backend.ipad_sdk_jwt import (
    MeetingSDKSigningCredentials,
    MeetingSDKTokenConfigError,
    issue_native_participant_jwt,
)


def unpack_segment(segment):
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


class MeetingSDKJWTTests(unittest.TestCase):
    def setUp(self):
        self.credentials = MeetingSDKSigningCredentials("test-sdk-client-id", "test-only-never-real-secret")

    def test_signed_participant_claims_and_hmac(self):
        token = issue_native_participant_jwt(self.credentials, "12345678901", now=1_800_000_000)
        header, claims, signature = token.split(".")
        self.assertEqual(unpack_segment(header), {"alg": "HS256", "typ": "JWT"})
        self.assertEqual(unpack_segment(claims), {
            "appKey": "test-sdk-client-id", "mn": "12345678901", "role": 0,
            "iat": 1_800_000_000, "exp": 1_800_001_800, "tokenExp": 1_800_001_800,
        })
        expected = hmac.new(self.credentials.client_secret.encode(),
                            f"{header}.{claims}".encode(), hashlib.sha256).digest()
        self.assertEqual(base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)), expected)

    def test_rejects_bad_meeting_number(self):
        for bad in ("", "123", "123456789 0", "not a number", "1234567890\n", "12345678901234", "１２３４５６７８９"):
            with self.subTest(bad=bad), self.assertRaises(MeetingSDKTokenConfigError):
                issue_native_participant_jwt(self.credentials, bad, now=1_800_000_000)

    def test_rejects_out_of_range_expiry(self):
        for seconds in (0, 1799, 7201, True, 0.5):
            with self.subTest(seconds=seconds), self.assertRaises(MeetingSDKTokenConfigError):
                issue_native_participant_jwt(self.credentials, "12345678901", now=1_800_000_000, duration_seconds=seconds)

    def test_rejects_missing_client_secret(self):
        with self.assertRaises(MeetingSDKTokenConfigError):
            MeetingSDKSigningCredentials("test-client", "")

    def test_rejects_missing_client_id(self):
        with self.assertRaises(MeetingSDKTokenConfigError):
            MeetingSDKSigningCredentials("", "secret")

    def test_rejects_bad_timestamps(self):
        for bad in (0, -1, 1.4, True):
            with self.subTest(timestamp=bad), self.assertRaises(MeetingSDKTokenConfigError):
                issue_native_participant_jwt(self.credentials, "12345678901", now=bad)

    def test_signature_is_sensitive_to_signing_secret(self):
        token1 = issue_native_participant_jwt(self.credentials, "12345678901", now=1_800_000_000)
        token2 = issue_native_participant_jwt(MeetingSDKSigningCredentials("test-sdk-client-id", "different-test-secret"),
                                               "12345678901", now=1_800_000_000)
        self.assertNotEqual(token1, token2)

    def test_caller_must_provide_credentials_object(self):
        with self.assertRaises(MeetingSDKTokenConfigError):
            issue_native_participant_jwt(None, "12345678901", now=1_800_000_000)


if __name__ == "__main__":
    unittest.main()
