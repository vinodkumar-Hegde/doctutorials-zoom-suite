"""Automatic imported-Admin class reservations, without duplicate manual entry."""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from assigned_channel_plan import enrich_admin_schedule, selected_session
from existing_admin_sessions import ExistingAdminSessions
from controller import ControlState, handler_factory
from engine import RecorderError


class FakeCaptureEngine:
    def __init__(self, *, test_media=True):
        mode='TEST MEDIA — NOT ZOOM' if test_media else 'WINDOWS INPUT (NOT VERIFIED ZOOM)'
        kind='lavfi' if test_media else 'gdigrab'
        self.channels={str(i):{'configured':True,'mode':mode,
            'screen':{'kind':kind},'faculty':{'kind':kind},
            'audio':{'kind':'lavfi' if test_media else 'wasapi_loopback'}} for i in range(1,5)}
        self.started=[]
    def status(self):
        return [{'channel':str(i),'configured':True,'sourceMode':self.channels[str(i)]['mode'],
                 'state':'idle','last':None} for i in range(1,5)]
    def recordings(self):return []
    def start(self,channel,meta):
        self.started.append((channel,meta))
        return {'channel':channel,'id':'fake-test-job','state':'starting'}


def session(i,start=1800000000,end=1800003600):
    return dict(sessionId=f'original-{i}', facultyId=f'fac-{i}',course='NEET SS',
                subject='Pathology',topic='Test',startsAt=start,endsAt=end)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.status=FakeCaptureEngine().status()
    def plan(self,sessions,now=1800001000):
        return enrich_admin_schedule({'state':'existing_admin','sessions':sessions},self.status,now=now)
    def test_one_current_class_automatically_binds_channel_one(self):
        p=self.plan([session(1)])
        self.assertEqual(p['sessions'][0]['plannedChannel'],'1')
        self.assertEqual(p['channels'][0]['assignedSession']['sessionId'],'original-1')
        self.assertFalse(p['channels'][0]['zoomMediaConnected'])
        self.assertFalse(p['channels'][0]['captureReady'])
        self.assertIsNone(p['channels'][1]['assignedSession'])
    def test_four_overlapping_fifth_rejected_without_duplicate_channel(self):
        p=self.plan([session(i) for i in range(5,0,-1)])
        self.assertEqual([v['plannedChannel'] for v in p['sessions']],['1','2','3','4',None])
        self.assertEqual(p['sessions'][4]['assignmentState'],'capacity_exceeded')
    def test_sequential_classes_reuse_channel_one(self):
        p=self.plan([session(2,1800003600,1800007200),session(1)],now=1800004000)
        self.assertEqual([v['plannedChannel'] for v in p['sessions']],['1','1'])
        self.assertEqual(p['channels'][0]['assignedSession']['sessionId'],'original-2')
    def test_active_current_gets_priority_over_future(self):
        p=self.plan([session(1),session(2,1800003600,1800007200)])
        self.assertEqual(p['channels'][0]['assignedSession']['sessionId'],'original-1')
    def test_no_start_outside_window_and_capacity(self):
        p=self.plan([session(1)])
        with self.assertRaisesRegex(RecorderError,'outside its scheduled window'):
            selected_session(p,'original-1',now=1800007200)
        self.assertEqual(selected_session(p,'original-1',now=1800000100)['plannedChannel'],'1')
        with self.assertRaisesRegex(RecorderError,'not present'):
            selected_session(p,'original-unknown',now=1800000100)
    def test_input_is_not_mutated(self):
        s=session(1)
        p=self.plan([s])
        self.assertNotIn('plannedChannel',s)
        self.assertEqual(p['mediaState'],'zoom_not_connected')


class PlanHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'original.sqlite3'
        self.original=session(1,start=int(time.time())-300,end=int(time.time())+3300)
        with sqlite3.connect(self.db) as db:
            db.execute('''CREATE TABLE sessions (session_id TEXT PRIMARY KEY,faculty_id TEXT,
                course TEXT,subject TEXT,topic TEXT,starts_at INTEGER,ends_at INTEGER,
                meeting_id TEXT,meeting_passcode TEXT)''')
            r=self.original
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',
                       (r['sessionId'],r['facultyId'],r['course'],r['subject'],r['topic'],
                        r['startsAt'],r['endsAt'],'9876543210','never-return-this-passcode'))
        self.engine=FakeCaptureEngine()
        self.state=ControlState(self.engine,'a-long-password-for-test',ExistingAdminSessions(self.db))
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler_factory(self.state))
        worker=threading.Thread(target=self.server.serve_forever,daemon=True);worker.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'
    def req(self,path,body=None,token=None):
        headers={'Authorization':'Bearer '+token} if token else {}
        if body is not None:headers['Content-Type']='application/json'
        return urlopen(Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers),timeout=5)
    def login(self):
        return json.load(self.req('/api/login',{'password':'a-long-password-for-test'}))['token']
    def test_authenticated_auto_mapping_never_leaks_meeting_secrets(self):
        with self.assertRaises(HTTPError) as err:self.req('/api/channels')
        self.assertEqual(err.exception.code,401)
        tok=self.login()
        channels=json.load(self.req('/api/channels',token=tok))
        self.assertEqual(channels['channels'][0]['assignedSession']['sessionId'],self.original['sessionId'])
        s=json.load(self.req('/api/sessions',token=tok))
        self.assertEqual(s['sessions'][0]['plannedChannel'],'1')
        serialized=json.dumps((channels,s))
        self.assertNotIn('never-return-this-passcode',serialized)
        self.assertNotIn('9876543210',serialized)
    def test_fake_capture_rejected_and_no_job_created(self):
        tok=self.login()
        with self.assertRaises(HTTPError) as resp:
            self.req('/api/start-assigned',{'sessionId':self.original['sessionId'],'consentConfirmed':True},tok)
        self.assertEqual(resp.exception.code,400)
        self.assertEqual([],self.engine.started)
    def test_consent_is_required_even_for_real_configured_input(self):
        self.engine=FakeCaptureEngine(test_media=False)
        self.state.engine=self.engine
        tok=self.login()
        with self.assertRaises(HTTPError) as resp:
            self.req('/api/start-assigned',{'sessionId':self.original['sessionId']},tok)
        self.assertEqual(resp.exception.code,400)
        self.assertEqual([],self.engine.started)
    def test_manual_metadata_cannot_impersonate_real_class(self):
        tok=self.login()
        body={'channel':'1','sessionId':self.original['sessionId'],
              'course':'TEST MEDIA','subject':'No','topic':'No','faculty':'No','facultyId':'test'}
        with self.assertRaises(HTTPError) as resp:self.req('/api/start',body,tok)
        self.assertEqual(resp.exception.code,400)
        self.assertEqual([],self.engine.started)
    def test_actual_configured_capture_uses_imported_metadata_no_manual_entry(self):
        self.engine=FakeCaptureEngine(test_media=False)
        self.state.engine=self.engine
        tok=self.login()
        result=json.load(self.req('/api/start-assigned',{'sessionId':self.original['sessionId'],'consentConfirmed':True},tok))
        self.assertEqual(result['channel'],'1')
        self.assertEqual(self.engine.started[0][1]['course'],'NEET SS')
        self.assertEqual(self.engine.started[0][1]['faculty'],self.original['facultyId'])
        self.assertNotIn('meeting_id',self.engine.started[0][1])

if __name__=='__main__':unittest.main()
