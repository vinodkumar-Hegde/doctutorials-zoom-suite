"""Windows-local Admin schedule and API contract tests, no Zoom or Mac required."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from local_sessions import LocalSessions, ScheduleError
from controller import ControlState, handler_factory


class FakeEngine:
    """No media source is started by scheduling tests."""
    def status(self): return []
    def recordings(self): return []


class AdminTests(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.path = Path(td.name) / 'recorder' / 'admin.sqlite3'
        self.store = LocalSessions(self.path)
        self.details = dict(
            facultyId='faculty_01', faculty='Dr Example', course='Medicine',
            subject='Cardiology', topic='Cardiac Cycle', startsAt=1800000000,
            endsAt=1800003600, channel='1',
        )

    def test_create_list_persists_after_restart(self):
        item = self.store.create(self.details)
        self.assertEqual(item['state'], 'scheduled')
        self.assertEqual(item['channel'], '1')
        self.assertEqual([item], LocalSessions(self.path).list())
        self.assertEqual(self.store.snapshot()['state'], 'local_windows')

    def test_reservation_overlaps_only_on_same_channel(self):
        self.store.create(self.details)
        with self.assertRaisesRegex(ScheduleError, 'already occupies'):
            self.store.create({**self.details, 'startsAt':1800001200, 'endsAt':1800004800})
        self.assertEqual(self.store.create({**self.details, 'channel':'2'})['channel'], '2')
        self.assertEqual(self.store.create({**self.details, 'startsAt':1800003600, 'endsAt':1800007200})['channel'],'1')

    def test_cancel_retains_record_and_frees_channel(self):
        item = self.store.create(self.details)
        self.assertEqual(self.store.cancel(item['sessionId'])['state'], 'cancelled')
        with self.assertRaisesRegex(ScheduleError,'not found'):
            self.store.cancel(item['sessionId'])
        self.assertEqual(self.store.create(self.details)['state'], 'scheduled')
        self.assertEqual(len(self.store.list()), 2)

    def test_invalid_data_rejected(self):
        bad_cases = (
            {'facultyId':'../escape'}, {'topic':''}, {'startsAt':'soon'},
            {'endsAt':1800000000}, {'channel':'9'}, {'course':'x'*140},
            {'faculty':'Dr\nInjection'}, {'endsAt':1800000000+25*3600},
        )
        for patch in bad_cases:
            with self.subTest(patch=patch), self.assertRaises(ScheduleError):
                self.store.create({**self.details, **patch})
        self.assertEqual(self.store.list(),[])

    def test_schedule_cannot_hold_zoom_secrets(self):
        private = {**self.details,'meetingPasscode':'NOT-TO-STORE',
                   'meetingId':'99999999999','zoomSdkSecret':'NOT-TO-STORE'}
        item=self.store.create(private)
        self.assertEqual(set(item.keys()), {'facultyId','faculty','course','subject',
                                             'topic','startsAt','endsAt','channel','sessionId','state'})
        raw=self.path.read_bytes()
        for sensitive in (b'NOT-TO-STORE',b'99999999999'):
            self.assertNotIn(sensitive,raw)


class AdminHttpTests(AdminTests):
    def setUp(self):
        super().setUp()
        self.state=ControlState(FakeEngine(),'strong-local-admin-password',self.store)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler_factory(self.state))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'

    def request(self,path,body=None,token=None):
        headers={}
        if token: headers['Authorization']='Bearer '+token
        if body is not None: headers['Content-Type']='application/json'
        request=Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        return urlopen(request,timeout=8)

    def test_schedule_routes_require_auth(self):
        for path,payload in (('/api/sessions',None),('/api/sessions/create',self.details),
                             ('/api/sessions/cancel',{'sessionId':'s-'+'a'*24})):
            with self.subTest(path=path), self.assertRaises(HTTPError) as response:
                self.request(path,payload)
            self.assertEqual(response.exception.code,401)
        self.assertEqual(self.store.list(),[])

    def test_admin_creates_and_cancels_from_http(self):
        token=json.load(self.request('/api/login',{'password':'strong-local-admin-password'}))['token']
        created=json.load(self.request('/api/sessions/create',self.details,token))['session']
        sessions=json.load(self.request('/api/sessions',token=token))
        self.assertEqual(sessions['state'],'local_windows')
        self.assertEqual(sessions['sessions'],[created])
        result=json.load(self.request('/api/sessions/cancel',{'sessionId':created['sessionId']},token))
        self.assertEqual(result['session']['state'],'cancelled')
        self.assertEqual(self.store.list()[0]['state'],'cancelled')

    def test_duplicate_channel_http_conflict(self):
        token=json.load(self.request('/api/login',{'password':'strong-local-admin-password'}))['token']
        self.request('/api/sessions/create',self.details,token)
        with self.assertRaises(HTTPError) as response:
            self.request('/api/sessions/create',self.details,token)
        self.assertEqual(response.exception.code,400)
        self.assertEqual(len(self.store.list()),1)


if __name__=='__main__':unittest.main()
