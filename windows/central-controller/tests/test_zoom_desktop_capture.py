"""Offline Windows desktop capture safety checks (NOT live Zoom acceptance)."""
from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest import mock
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
import threading

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from controller import ControlState, handler_factory, build_demo_config
from engine import Engine,RecorderError,source_args
from zoom_desktop_capture import (ZoomDesktopController,ZoomWindow,ZoomDesktopUnavailable,
    private_meeting_for,capture_sources,single_zoom_window)
from existing_admin_sessions import ExistingAdminSessions

class DesktopSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.public=self.root/'public.sqlite3'
        self.private=self.root/'private.sqlite3'
        self.now=int(time.time())
        self.item={'sessionId':'session_001','facultyId':'sandbox-faculty','course':'NEET SS',
                   'subject':'Pathology','topic':'Test','startsAt':self.now-30,
                   'endsAt':self.now+800,'plannedChannel':'1'}
        with sqlite3.connect(self.private) as db:
            db.execute('''CREATE TABLE sessions(session_id TEXT PRIMARY KEY,faculty_id TEXT,
                course TEXT,subject TEXT,topic TEXT,starts_at INTEGER,ends_at INTEGER,
                meeting_id TEXT,meeting_passcode TEXT)''')
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',
                       (self.item['sessionId'],self.item['facultyId'],self.item['course'],
                        self.item['subject'],self.item['topic'],self.item['startsAt'],
                        self.item['endsAt'],'12345678901','aPass#1'))
        self.window=ZoomWindow(10001,1280,720)

    def test_real_admin_meeting_lookup_not_public(self):
        self.assertEqual('12345678901',private_meeting_for(self.private,self.item)['meeting_id'])
        with self.assertRaises(ZoomDesktopUnavailable):private_meeting_for(self.private,{**self.item,'facultyId':'other'})
        self.assertEqual('12345678901',private_meeting_for(self.private,{**self.item,'endsAt':self.item['endsAt']+1})['meeting_id'])
        with self.assertRaises(ZoomDesktopUnavailable):private_meeting_for(self.private,{**self.item,'topic':'different'})
        with self.assertRaises(ZoomDesktopUnavailable):private_meeting_for(self.root/'missing.sqlite3',self.item)
        self.assertFalse((self.root/'missing.sqlite3').exists())

    def test_launch_does_not_return_join_secrets(self):
        launched=[]
        c=ZoomDesktopController(self.private,finder=lambda:[self.window],launcher=launched.append)
        response=c.open(self.item)
        self.assertEqual(response['state'],'launch_requested')
        self.assertEqual(len(launched),1)
        self.assertIn('confno=12345678901',launched[0])
        self.assertIn('pwd=aPass%231',launched[0])
        self.assertNotIn('12345678901',str(response)+str(c.status()))
        self.assertNotIn('aPass',str(response)+str(c.status()))
        self.assertEqual(c.status()['windowState'],'single')
        self.assertEqual(c.status()['openedSessionId'],'session_001')

    def test_capture_source_has_window_handle_not_entire_desktop(self):
        data=capture_sources(self.window)
        self.assertEqual(data['mode'].split(' — ')[0],'ZOOM DESKTOP WINDOW')
        self.assertEqual(data['screen']['window_hwnd'],10001)
        self.assertEqual(data['faculty']['kind'],'gdigrab')
        self.assertEqual(data['audio']['kind'],'wasapi_loopback')
        self.assertEqual(len(data['faculty']['crop']),4)
        self.assertNotIn('desktop',repr(data['screen']))
        with mock.patch('engine.sys.platform','win32'):
            args=source_args(data['screen'],fps=25,video=True)
        self.assertEqual(args[-1],'hwnd=0x2711')
        with mock.patch('engine.sys.platform','win32'):
            with self.assertRaises(RecorderError):source_args({'kind':'gdigrab','window_hwnd':-1},fps=25,video=True)

    def test_no_ambiguous_or_minimized_windows_for_capture(self):
        with self.assertRaises(ZoomDesktopUnavailable):single_zoom_window([])
        with self.assertRaises(ZoomDesktopUnavailable):single_zoom_window([self.window,self.window])

    def test_capture_requires_consent_exact_open_and_one_worker(self):
        engine=Engine(build_demo_config(self.root/'engine'))
        self.addCleanup(engine.close)
        c=ZoomDesktopController(self.private,finder=lambda:[self.window],launcher=lambda _:None)
        with self.assertRaises(ZoomDesktopUnavailable):c.start_capture(engine,self.item,True)
        c.open(self.item)
        with self.assertRaises(ZoomDesktopUnavailable):c.start_capture(engine,self.item,False)
        class Live:
            def poll(self):return None
        engine.processes['2']=Live()
        with self.assertRaises(ZoomDesktopUnavailable):c.start_capture(engine,self.item,True)
        engine.processes.clear()
        with mock.patch.object(engine,'start',return_value={'state':'starting'}) as fake:
            actual=c.start_capture(engine,self.item,True)
            self.assertEqual(actual['state'],'starting')
            self.assertEqual(fake.call_args.args[0],'1')
            self.assertEqual(engine.channels['1']['screen']['window_hwnd'],10001)
        with mock.patch.object(engine,'start',side_effect=RecorderError('no audio')):
            with self.assertRaises(RecorderError):c.start_capture(engine,self.item,True)
            # Restores previous configured input, does not advertise succeeded.
            self.assertEqual(engine.channels['1']['screen']['window_hwnd'],10001)

    def test_preview_of_only_zoom_window_uses_hwnd_not_desktop(self):
        engine=Engine(build_demo_config(self.root/'engine'))
        self.addCleanup(engine.close)
        c=ZoomDesktopController(self.private,finder=lambda:[self.window],launcher=lambda _:None)
        with self.assertRaises(ZoomDesktopUnavailable):c.preview(engine,self.item)
        c.open(self.item)
        screenshot=b'\x89PNG\r\n\x1a\n' + b'safe-preview'
        with mock.patch('zoom_desktop_capture.sys.platform','win32'):
            with mock.patch('zoom_desktop_capture.subprocess.run',return_value=mock.Mock(returncode=0,stdout=screenshot)) as run:
                self.assertEqual(c.preview(engine,self.item),screenshot)
                self.assertIn('hwnd=0x2711',run.call_args.args[0])
                self.assertNotIn('desktop',run.call_args.args[0])
            with mock.patch('zoom_desktop_capture.subprocess.run',return_value=mock.Mock(returncode=1,stdout=b'')):
                with self.assertRaises(ZoomDesktopUnavailable):c.preview(engine,self.item)

    def test_private_export_is_offline_and_non_overwriting(self):
        from export_private_zoom_registry import export
        src=self.root/'mac_original.sqlite3'
        with sqlite3.connect(src) as db:
            db.execute('CREATE TABLE sessions(session_id TEXT PRIMARY KEY,faculty_id TEXT,course TEXT,subject TEXT,topic TEXT,starts_at INTEGER,ends_at INTEGER,meeting_id TEXT,meeting_passcode TEXT)')
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',
                       (self.item['sessionId'],self.item['facultyId'],self.item['course'],
                        self.item['subject'],self.item['topic'],self.item['startsAt'],
                        self.item['endsAt'],'12345678901','aPass#1'))
        out=self.root/'private-export.sqlite3'
        self.assertEqual(export(src,out),1)
        self.assertEqual(private_meeting_for(out,self.item)['passcode'],'aPass#1')
        with self.assertRaises(RuntimeError):export(src,out)
        self.assertTrue(out.is_file())

    def test_authenticated_local_api_controls_no_secret_disclosure(self):
        with sqlite3.connect(self.public) as db:
            db.execute('''CREATE TABLE sessions(session_id TEXT PRIMARY KEY,faculty_id TEXT,
                course TEXT,subject TEXT,topic TEXT,starts_at INTEGER,ends_at INTEGER)''')
            db.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?)',
                (self.item['sessionId'],self.item['facultyId'],self.item['course'],self.item['subject'],
                 self.item['topic'],self.item['startsAt'],self.item['endsAt']))
        engine=Engine(build_demo_config(self.root/'engine'))
        self.addCleanup(engine.close)
        state=ControlState(engine,'super-secret-password',ExistingAdminSessions(self.public))
        launched=[]
        state.desktop=ZoomDesktopController(self.private,finder=lambda:[self.window],launcher=launched.append)
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_factory(state))
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base='http://127.0.0.1:'+str(server.server_address[1])
        def post(path,body,token=None):
            headers={'Content-Type':'application/json'}
            if token:headers['Authorization']='Bearer '+token
            req=Request(base+path,headers=headers,data=json.dumps(body).encode())
            with urlopen(req,timeout=5) as response:return json.load(response)
        with self.assertRaises(HTTPError) as caught:
            post('/api/desktop/open',{'sessionId':self.item['sessionId']})
        self.assertEqual(caught.exception.code,401)
        token=post('/api/login',{'password':'super-secret-password'})['token']
        res=post('/api/desktop/open',{'sessionId':self.item['sessionId']},token)
        self.assertEqual(res['state'],'launch_requested')
        self.assertNotIn('12345678901',str(res))
        with urlopen(Request(base+'/api/sessions',headers={'Authorization':'Bearer '+token}),timeout=5) as r:
            data=json.load(r)
        self.assertEqual(data['desktopCapture']['captureReady'],True)
        self.assertNotIn('aPass',str(data))
        with self.assertRaises(HTTPError) as caught:
            post('/api/desktop/record',{'sessionId':self.item['sessionId'],'consentConfirmed':False},token)
        self.assertEqual(caught.exception.code,400)

if __name__=='__main__':unittest.main()
