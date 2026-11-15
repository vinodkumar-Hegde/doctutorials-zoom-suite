"""Original DocTutorials Admin DB integration; verifies no duplicate entry or leaked Zoom secrets."""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from existing_admin_sessions import ExistingAdminSessions
from controller import ControlState, handler_factory

class EmptyEngine:
    def status(self): return []
    def recordings(self): return []

class ExistingAdminTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db=Path(temp.name)/'demo-live-sessions.sqlite3'
        self.store=ExistingAdminSessions(self.db)

    def setup_original_db(self):
        with sqlite3.connect(self.db) as con:
            con.execute('''CREATE TABLE sessions (session_id TEXT PRIMARY KEY,
                faculty_id TEXT NOT NULL, course TEXT NOT NULL,
                subject TEXT NOT NULL, topic TEXT NOT NULL, starts_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL, meeting_id TEXT NOT NULL,
                meeting_passcode TEXT NOT NULL)''')
            con.execute('''INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)''',
                ('original-session','faculty-1','Medicine','Cardiology','Physiology',
                 1800000000,1800003600,'12345678901','private-meeting-passcode'))

    def test_missing_db_does_not_create_empty_fake_schedule(self):
        reply=self.store.snapshot()
        self.assertEqual(reply['state'],'admin_data_missing')
        self.assertEqual(reply['sessions'],[])
        self.assertFalse(self.db.exists())

    def test_original_db_read_only_and_secrets_excluded(self):
        self.setup_original_db()
        before=self.db.read_bytes()
        reply=self.store.snapshot()
        self.assertEqual(reply['state'],'existing_admin')
        self.assertEqual(reply['sessions'],[{
            'sessionId':'original-session','facultyId':'faculty-1',
            'course':'Medicine','subject':'Cardiology','topic':'Physiology',
            'startsAt':1800000000,'endsAt':1800003600
        }])
        self.assertNotIn('12345678901',json.dumps(reply))
        self.assertNotIn('private-meeting-passcode',json.dumps(reply))
        self.assertEqual(self.db.read_bytes(),before)

    def test_live_reflects_admin_db_edits_without_restart(self):
        self.setup_original_db()
        self.assertEqual(len(self.store.snapshot()['sessions']),1)
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE sessions SET course='Anatomy' WHERE session_id='original-session'")
        self.assertEqual(self.store.snapshot()['sessions'][0]['course'],'Anatomy')

    def test_bad_schema_returns_sanitized_status(self):
        self.db.write_text('not a sqlite database',encoding='utf8')
        reply=self.store.snapshot()
        self.assertEqual(reply['state'],'admin_data_unavailable')
        self.assertNotIn('not a sqlite',str(reply))

    def test_symlink_refused(self):
        self.setup_original_db()
        symlink=self.db.with_name('linked.sqlite3')
        try:symlink.symlink_to(self.db)
        except (OSError,NotImplementedError):self.skipTest('symlinks unsupported')
        self.assertEqual(ExistingAdminSessions(symlink).snapshot()['state'],'admin_data_missing')

    def test_http_does_not_allow_duplicate_assignment(self):
        self.setup_original_db()
        state=ControlState(EmptyEngine(),'strong-local-admin-password',self.store)
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_factory(state))
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base='http://127.0.0.1:'+str(server.server_address[1])
        def request(path,data=None,token=None):
            b=json.dumps(data).encode() if data is not None else None
            headers={'Content-Type':'application/json'} if data is not None else {}
            if token:headers['Authorization']='Bearer '+token
            return urlopen(Request(base+path,data=b,headers=headers),timeout=5)
        with self.assertRaises(HTTPError) as noauth:
            request('/api/sessions')
        self.assertEqual(noauth.exception.code,401)
        token=json.load(request('/api/login',{'password':'strong-local-admin-password'}))['token']
        reply=json.load(request('/api/sessions',token=token))
        self.assertEqual(reply['sessions'][0]['sessionId'],'original-session')
        for path in ('/api/sessions/create','/api/sessions/cancel'):
            with self.subTest(path=path),self.assertRaises(HTTPError) as refused:
                request(path,{'sessionId':'original-session'},token=token)
            self.assertEqual(refused.exception.code,405)
        self.assertEqual(len(self.store.snapshot()['sessions']),1)

if __name__=='__main__': unittest.main()
