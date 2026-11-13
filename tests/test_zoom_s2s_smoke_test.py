import base64
import io
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
from urllib.error import HTTPError

SOURCE = Path(__file__).resolve().parents[1] / 'backend' / 'zoom_s2s_smoke_test.py'
spec = importlib.util.spec_from_file_location('zoom_s2s_smoke_test', SOURCE)
import sys
z = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = z
spec.loader.exec_module(z)


class FakeResponse:
    def __init__(self, body: str): self.body = body.encode('utf-8')
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def read(self, size=-1): return self.body[:size]


class ZoomSmokeTestTests(unittest.TestCase):
    def test_oauth_token_grant_uses_post_basic_and_form(self):
        seen = []
        def opener(req, timeout):
            seen.append(req)
            return FakeResponse('{"access_token":"example-token", "expires_in":3600}')
        c = z.ZoomReadOnlyClient(z.ZoomCredentials('my-account','my-id','my-secret'), opener)
        c.authenticate()
        self.assertEqual(seen[0].get_method(), 'POST')
        self.assertEqual(seen[0].full_url, z.TOKEN_URL)
        self.assertIn(b'grant_type=account_credentials', seen[0].data)
        self.assertIn(b'account_id=my-account', seen[0].data)
        self.assertEqual(seen[0].get_header('Authorization'), 'Basic ' + base64.b64encode(b'my-id:my-secret').decode())

    def test_api_reads_use_only_get_and_bearer(self):
        seen = []
        def opener(req, timeout):
            seen.append(req)
            return FakeResponse('{"users":[],"next_page_token":""}')
        c = z.ZoomReadOnlyClient(z.ZoomCredentials('a','b','c'), opener)
        c._access_token='sample-only'
        self.assertEqual(c.list_users(), [])
        self.assertEqual(seen[0].get_method(), 'GET')
        self.assertIn('status=active', seen[0].full_url)
        self.assertEqual(seen[0].get_header('Authorization'), 'Bearer sample-only')

    def test_paginates_next_page_token(self):
        seen=[]
        def opener(req, timeout):
            seen.append(req.full_url)
            if len(seen)==1:
                return FakeResponse('{"webinars":[{"id":101}], "next_page_token":"abc+123"}')
            return FakeResponse('{"webinars":[{"id":102}], "next_page_token":""}')
        c=z.ZoomReadOnlyClient(z.ZoomCredentials('a','b','c'),opener)
        c._access_token='token'
        self.assertEqual([x['id'] for x in c.list_webinars('host-id')], [101,102])
        self.assertIn('next_page_token=abc%2B123', seen[1])

    def test_http_error_does_not_expose_private_body(self):
        def opener(req, timeout):
            raise HTTPError(req.full_url,403,'Forbidden',{},io.BytesIO(b'private-token-and-email@example.com'))
        c=z.ZoomReadOnlyClient(z.ZoomCredentials('account','id','secret'),opener)
        with self.assertRaises(z.SmokeTestError) as cm: c.authenticate()
        self.assertIn('HTTP 403',str(cm.exception))
        self.assertNotIn('private-token',str(cm.exception))
        self.assertNotIn('email',str(cm.exception))

    def test_rejects_unapproved_url_path(self):
        c=z.ZoomReadOnlyClient(z.ZoomCredentials('a','b','c'),lambda *_: None)
        c._access_token='token'
        with self.assertRaises(z.SmokeTestError): c.get('https://unapproved.example/')
        with self.assertRaises(z.SmokeTestError): c.get('//unapproved.example/')

    def test_eligible_host_filter(self):
        data=[{'id':'a','type':2},{'id':'b','type':1},{'id':'c','type':3},{'id':'','type':2}]
        self.assertEqual([u['id'] for u in z.eligible_users(data)],['a','c'])

    def test_exactly_four_autoselected(self):
        choices=[{'id':str(x)} for x in range(4)]
        self.assertEqual(z.choose_hosts(choices), choices)

    def test_insufficient_hosts_rejected(self):
        with self.assertRaises(z.SmokeTestError): z.choose_hosts([{'id':'1'}])

    def test_empty_api_shape_fails_closed(self):
        c=z.ZoomReadOnlyClient(z.ZoomCredentials('a','b','c'), lambda req,timeout:FakeResponse('{}'))
        c._access_token='token'
        with self.assertRaises(z.SmokeTestError):c.list_users()


    def test_sandbox_one_basic_user_checks_meetings_only(self):
        class SandboxClient:
            calls = []
            def authenticate(self): self.calls.append("oauth")
            def list_users(self):
                self.calls.append("users")
                return [{"id": "sandbox-id", "type": 1}]
            def list_meetings(self, user_id):
                self.calls.append("meetings")
                self.assert_host_id = user_id
                return [{"id": 101}]
            def check_meeting_detail(self, meeting_id):
                self.calls.append("detail")
                self.assert_meeting_id = meeting_id
            def list_webinars(self, user_id):
                raise AssertionError("Sandbox must not invoke webinar endpoints")

        client = SandboxClient()
        output = io.StringIO()
        with patch("sys.stdout", output):
            status = z.run(client, sandbox_single_user=True)
        self.assertEqual(status, 0)
        self.assertEqual(client.calls, ["oauth", "users", "meetings", "detail"])
        self.assertEqual(client.assert_host_id, "sandbox-id")
        self.assertEqual(client.assert_meeting_id, 101)
        self.assertIn("NOT four-host", output.getvalue())
        self.assertIn("webinars=NOT TESTED", output.getvalue())

    def test_sandbox_basic_user_with_no_meetings_skips_detail(self):
        class SandboxClient:
            def authenticate(self): pass
            def list_users(self): return [{"id": "sandbox-id", "type": 1}]
            def list_meetings(self, user_id): return []
            def check_meeting_detail(self, meeting_id):
                raise AssertionError("No detail GET when there are no meetings")

        with patch("sys.stdout", io.StringIO()) as fake_out:
            self.assertEqual(z.run(SandboxClient(), sandbox_single_user=True), 0)
            self.assertIn("meeting detail=SKIPPED", fake_out.getvalue())

    def test_sandbox_rejects_multi_user_organization(self):
        class SandboxClient:
            def authenticate(self): pass
            def list_users(self):
                return [{"id": "user1", "type": 1}, {"id": "user2", "type": 1}]
        with patch("sys.stdout", io.StringIO()):
            with self.assertRaisesRegex(z.SmokeTestError, "requires exactly one active user"):
                z.run(SandboxClient(), sandbox_single_user=True)

    def test_default_mode_rejects_single_basic_user(self):
        class SandboxClient:
            def authenticate(self): pass
            def list_users(self): return [{"id": "basic-user", "type": 1}]
        with patch("sys.stdout", io.StringIO()):
            with self.assertRaisesRegex(z.SmokeTestError, "expected at least 4"):
                z.run(SandboxClient())

if __name__=='__main__':
    unittest.main()
