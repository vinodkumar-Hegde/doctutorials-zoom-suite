import unittest
from backend.meetings_service import SandboxMeetingsService, safe_meeting
from backend.zoom_s2s_smoke_test import SmokeTestError


class FakeZoom:
    def __init__(self, *, users=None, meetings=None, details=None):
        self.users = [{"id": "free-user", "type": 1}] if users is None else users
        self.meetings = [{"id": 42, "topic": "Sandbox lesson", "join_url": "private-link"}] if meetings is None else meetings
        self.details = {"id": 42, "topic": "Sandbox lesson", "join_url": "private-link"} if details is None else details
        self.auth_calls = 0
        self.calls = []

    def authenticate(self):
        self.auth_calls += 1

    def list_users(self):
        self.calls.append("users")
        return self.users

    def list_meetings(self, user_id):
        self.calls.append("meetings")
        if user_id != "free-user":
            raise AssertionError("wrong host")
        return self.meetings

    def get(self, path, *, purpose):
        self.calls.append("detail")
        if path != "/meetings/42":
            raise AssertionError("unexpected path")
        return self.details

    def list_webinars(self, user_id):
        raise AssertionError("Webinar API called during meetings-only phase")


class MeetingsServiceTests(unittest.TestCase):
    def test_safe_fields_never_include_join_url_or_ids(self):
        data = safe_meeting({
            "id": 42, "topic": "Topic", "join_url": "private-link",
            "password": "pass", "host_id": "host", "duration": 45,
            "timezone": "Asia/Kolkata", "start_time": "2026-11-16T09:00:00Z"
        }, 1)
        self.assertEqual(data, {
            "ref": 1, "topic": "Topic", "duration": 45,
            "timezone": "Asia/Kolkata", "start_time": "2026-11-16T09:00:00Z"
        })
        self.assertNotIn("join_url", str(data))
        self.assertNotIn("password", str(data))

    def test_reads_single_basic_meeting_and_detail(self):
        fake = FakeZoom()
        service = SandboxMeetingsService(fake)
        meetings = service.list_meetings()
        self.assertEqual(meetings[0]["ref"], 1)
        self.assertEqual(service.get_meeting(1)["topic"], "Sandbox lesson")
        self.assertEqual(fake.auth_calls, 1)
        self.assertEqual(fake.calls, ["users", "meetings", "meetings", "detail"])

    def test_empty_list_and_missing_detail_are_safe(self):
        fake = FakeZoom(meetings=[])
        service = SandboxMeetingsService(fake)
        self.assertEqual(service.list_meetings(), [])
        self.assertIsNone(service.get_meeting(1))
        self.assertNotIn("detail", fake.calls)

    def test_rejects_multi_user_account(self):
        fake = FakeZoom(users=[{"id":"free-user","type":1},{"id":"paid-user","type":2}])
        with self.assertRaises(SmokeTestError):
            SandboxMeetingsService(fake).list_meetings()

    def test_rejects_paid_account_even_if_one_user(self):
        fake = FakeZoom(users=[{"id":"free-user","type":2}])
        with self.assertRaises(SmokeTestError):
            SandboxMeetingsService(fake).list_meetings()

    def test_rejects_detail_when_zoom_returns_other_id(self):
        fake = FakeZoom(details={"id": 9999, "topic": "Other tenant"})
        service = SandboxMeetingsService(fake)
        with self.assertRaises(SmokeTestError):
            service.get_meeting(1)

    def test_rejects_invalid_local_meeting_ordinals(self):
        fake = FakeZoom()
        service = SandboxMeetingsService(fake)
        for index in (0, -1, 2000, True):
            self.assertIsNone(service.get_meeting(index))
        self.assertNotIn("detail", fake.calls)

    def test_refreshes_in_memory_token_on_renewal_interval(self):
        now = [0.0]
        fake = FakeZoom()
        service = SandboxMeetingsService(fake, clock=lambda: now[0])
        service.list_meetings()
        service.list_meetings()
        self.assertEqual(fake.auth_calls, 1)
        now[0] = 1201.0
        service.list_meetings()
        self.assertEqual(fake.auth_calls, 2)
        self.assertEqual(fake.calls.count("users"), 2)


if __name__ == "__main__":
    unittest.main()
