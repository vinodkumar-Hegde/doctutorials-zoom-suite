"""No-network diagnostic checks. Never use real app credentials in tests."""
import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import zoom_events_diagnostic as m


class DiagnosticTests(unittest.TestCase):
    def test_endpoint(self):
        self.assertTrue(m._valid_zoom_wss('wss://ws.zoom.us/ws?subscriptionId=abc'))
        for v in ('https://ws.zoom.us/ws?subscriptionId=abc',
                  'wss://ws.zoom.us.evil.com/ws?subscriptionId=abc',
                  'wss://other.zoom.us/ws?subscriptionId=abc',
                  'wss://ws.zoom.us/ws',
                  'wss://ws.zoom.us/ws?subscriptionId=abc&access_token=leak'):
            with self.subTest(url=v):
                self.assertFalse(m._valid_zoom_wss(v))

    def test_both_grants(self):
        response = MagicMock()
        response.read.return_value = json.dumps({'access_token':'fake-token'}).encode()
        context = MagicMock()
        context.__enter__.return_value = response
        with patch.object(m, 'urlopen', return_value=context) as fetch:
            self.assertEqual(m._request_token('id', 'secret', 'client_credentials', 'account')[0], 'PASS')
            self.assertEqual(fetch.call_args.args[0].data, b'grant_type=client_credentials')
            self.assertEqual(m._request_token('id', 'secret', 'account_credentials', 'account')[0], 'PASS')
            self.assertEqual(fetch.call_args.args[0].data,
                             b'grant_type=account_credentials&account_id=account')

    def test_http_failure_is_sanitized(self):
        err = HTTPError('https://zoom.us/oauth/token', 401, 'sensitive', {}, None)
        with patch.object(m, 'urlopen', side_effect=err):
            self.assertEqual(m._request_token('id','secret','account_credentials','account'),
                             ('HTTP 401', None))

    def test_ws_failure_sanitized(self):
        fake = MagicMock()
        fake.WebSocketBadStatusException = type('Bad', (Exception,), {})
        fake.WebSocketTimeoutException = type('Timeout', (Exception,), {})
        fake.create_connection.side_effect = RuntimeError('secret access_token=leak')
        with patch.dict(sys.modules, {'websocket':fake}):
            result = m._check_websocket('wss://ws.zoom.us/ws?subscriptionId=abc','private-token')
        self.assertEqual(result, 'CONNECTION FAILED (RuntimeError)')
        self.assertNotIn('leak', result)

    def test_no_values_are_printed(self):
        output = io.StringIO()
        with patch.dict(os.environ, {'ZOOM_EVENTS_CLIENT_ID':'unprintable-secret'}, clear=True), patch('sys.stdout', new=output):
            self.assertEqual(m.main(), 1)
        self.assertNotIn('unprintable-secret', output.getvalue())


if __name__ == '__main__':
    unittest.main()
