from __future__ import annotations
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import socket
import sqlite3
import ssl
import subprocess
import tempfile
import threading
import unittest

from mac_session_bridge import make_handler, read_public_sessions, QuietSessionServer
from session_feed import FeedError,SessionFeed,fetch_pinned_sessions,validate_public_sessions

SAMPLE={'sessionId':'class-001','facultyId':'sandbox-faculty','course':'Medicine','subject':'Cardiology',
        'topic':'Heart physiology','startsAt':1800000000,'endsAt':1800003600}

class SessionFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def _database(self):
        db=self.root/'admin.sqlite3'
        with sqlite3.connect(db) as cx:
            cx.execute('CREATE TABLE sessions (session_id TEXT,faculty_id TEXT,course TEXT,subject TEXT,topic TEXT,starts_at INT,ends_at INT,meeting_id TEXT,meeting_passcode TEXT)')
            cx.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',tuple(SAMPLE.values())+('123456789','sensitive-passcode'))
        return db

    def test_only_public_fields_leave_mac(self):
        items=read_public_sessions(self._database())
        self.assertEqual(items,[SAMPLE])
        self.assertNotIn('meeting',str(items).lower())
        self.assertNotIn('sensitive-passcode',str(items))

    def test_missing_db_is_empty(self):
        self.assertEqual(read_public_sessions(self.root/'missing.db'),[])

    def test_extra_meeting_details_are_rejected(self):
        payload=dict(SAMPLE,meetingPasscode='bad')
        with self.assertRaises(FeedError): validate_public_sessions({'sessions':[payload]})

    def test_rejects_bad_time_and_schema(self):
        for payload in [dict(SAMPLE,startsAt='tomorrow'),dict(SAMPLE,sessionId='../hack'),dict(SAMPLE,course='ok\n')]:
            with self.subTest(payload=payload),self.assertRaises(FeedError):validate_public_sessions({'sessions':[payload]})

    def test_without_pairing_show_disconnected(self):
        result=SessionFeed(self.root/'missing.json').snapshot()
        self.assertEqual(result['state'],'not_configured')
        self.assertEqual(result['sessions'],[])

    @unittest.skipUnless(__import__('shutil').which('openssl'),'openssl not installed in test environment')
    def test_pinned_https_exact_certificate_and_authorized_feed(self):
        cert=self.root/'cert.pem'; key=self.root/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost',
                        '-keyout',str(key),'-out',str(cert)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        database=self._database()
        secret='local-pairing-secret-long-enough'
        server=QuietSessionServer(('127.0.0.1',0),make_handler(database,secret))
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(cert),str(key))
        server.socket=ctx.wrap_socket(server.socket,server_side=True)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            fingerprint=hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert.read_text())).hexdigest()
            config={'url':f'https://127.0.0.1:{server.server_address[1]}/api/recorder/sessions',
                    'fingerprint':fingerprint,'token':secret}
            self.assertEqual(fetch_pinned_sessions(config),[SAMPLE])
            with self.assertRaisesRegex(FeedError,'fingerprint'):
                fetch_pinned_sessions(dict(config,fingerprint='0'*64))
            with self.assertRaisesRegex(FeedError,'authorization'):
                fetch_pinned_sessions(dict(config,token='bad-secret-with-at-least-20-chars'))
            for host in ['https://example.com/api/recorder/sessions','http://127.0.0.1/api/recorder/sessions',
                         'https://127.0.0.1/evil']:
                with self.assertRaises(FeedError):fetch_pinned_sessions(dict(config,url=host))
            # Ensure a locally paired controller gets real session cards via its scheduled refresh.
            localconf=self.root/'session-feed.json';localconf.write_text(json.dumps(config))
            self.assertEqual(SessionFeed(localconf).snapshot()['state'],'connected')
        finally:
            server.shutdown();server.server_close();t.join()

if __name__=='__main__':unittest.main()
