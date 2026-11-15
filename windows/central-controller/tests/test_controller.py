import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from controller import build_demo_config, handler_factory, ControlState
from engine import Engine, RecorderError, crop_filter, source_args, ensure_id, sha256_file
from http.server import ThreadingHTTPServer

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.config=build_demo_config(self.root/'storage')
        for c in self.config['channels'].values():
            c['demo_duration_seconds']=2
        self.engine=Engine(self.config)
        self.addCleanup(self.engine.close)
        self.meta=dict(sessionId='demo-lesson-01',facultyId='faculty01',faculty='Dr Example',
                       course='Medicine',subject='Cardiology',topic='Cardiac cycle')
    def wait_for(self,ids,timeout=40):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            jobs=[self.engine._job(rid) for rid in ids]
            if all(j['state'] in ('ready','failed','interrupted') for j in jobs):return jobs
            time.sleep(.2)
        self.fail('Recorder did not finish: '+repr([(j['id'],j['state']) for j in jobs]))
    def test_exactly_four_channels(self):
        self.assertEqual([c['channel'] for c in self.engine.status()],['1','2','3','4'])
    def test_rejects_unconfigured_and_does_not_falsely_start(self):
        self.engine.channels['1']['configured']=False
        with self.assertRaises(RecorderError):self.engine.start('1',self.meta)
        self.assertEqual([],self.engine.recordings())
    def test_rejects_bad_id(self):
        with self.assertRaises(RecorderError):ensure_id('../escape')
        with self.assertRaises(RecorderError):self.engine.start('1',{**self.meta,'sessionId':'../oops'})
    def test_crop_config_and_source_restrictions(self):
        self.assertEqual(crop_filter({'crop':[100,50,300,200]}),'crop=300:200:100:50,')
        with self.assertRaises(RecorderError):crop_filter({'crop':[-1,0,20,20]})
        with self.assertRaises(RecorderError):source_args({'kind':'network','url':'file:///etc/passwd'},fps=25,video=True)
    def test_one_actual_h264_aac_verified_and_archived(self):
        self.engine.nas=self.root/'nas'
        rid=self.engine.start('1',self.meta)['id']
        row=self.wait_for([rid])[0]
        self.assertEqual(row['state'],'ready',row['detail'])
        file=self.engine.media_path(rid)
        self.assertGreater(file.stat().st_size,5000)
        self.assertGreater(row['duration'],.5)
        self.assertEqual(sha256_file(file),row['sha256'])
        end=time.monotonic()+10
        while time.monotonic()<end and self.engine._job(rid)['archive_state']!='verified':time.sleep(.1)
        self.assertEqual(self.engine._job(rid)['archive_state'],'verified')
        dest=self.root/'nas'/self.meta['sessionId']/(rid+'.mp4')
        self.assertEqual(sha256_file(dest),sha256_file(file))
        with sqlite3.connect(self.engine.db_path) as db:
            row=db.execute('SELECT state,source FROM recordings WHERE recording_id=?',(rid,)).fetchone()
        self.assertEqual(row,('ready','recorder'))
    def test_four_simultaneous_recordings_isolated(self):
        jobs=[]
        for channel in ('1','2','3','4'):
            m={**self.meta,'sessionId':'demo-session-'+channel,'topic':'Teaching '+channel}
            jobs.append(self.engine.start(channel,m)['id'])
        finished=self.wait_for(jobs,timeout=70)
        self.assertTrue(all(j['state']=='ready' for j in finished),repr([(j['state'],j['detail']) for j in finished]))
        self.assertEqual(4,len({self.engine.media_path(j).resolve() for j in jobs}))
        self.assertEqual({'demo-session-1','demo-session-2','demo-session-3','demo-session-4'},
                         {j['session_id'] for j in finished})
        self.assertTrue(all(j['duration']>=1.0 for j in finished))
    def test_manual_stop_and_finalization(self):
        self.engine.channels['1']['demo_duration_seconds']=None
        rid=self.engine.start('1',self.meta)['id']
        deadline=time.monotonic()+12
        while self.engine._job(rid)['state']=='starting' and time.monotonic()<deadline:time.sleep(.2)
        self.assertEqual('recording',self.engine._job(rid)['state'])
        time.sleep(1)
        out=self.engine.stop('1')
        self.assertEqual(out['state'],'ready')
        self.assertTrue(self.engine.media_path(rid).exists())
    def test_interrupted_file_not_ready(self):
        rid=self.engine.start('1',self.meta)['id']
        p=self.engine.processes['1']
        p.kill();p.wait()
        result=self.wait_for([rid])[0]
        self.assertIn(result['state'],('failed','interrupted'))
        with self.assertRaises(RecorderError):self.engine.media_path(rid)
    def test_nas_failure_never_deletes_local(self):
        rid=self.engine.start('1',self.meta)['id']
        self.wait_for([rid])
        self.engine.nas=self.engine.media_path(rid) # existing file cannot contain directories
        self.engine.archive(rid)
        self.assertEqual(self.engine._job(rid)['archive_state'],'failed')
        self.assertTrue(self.engine.media_path(rid).exists())

class HTTPEngineTests(EngineTests):
    def setUp(self):
        super().setUp()
        self.state=ControlState(self.engine,'very-long-test-password')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),handler_factory(self.state))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'
    def request(self,path,body=None,token=None,headers=None):
        hs=headers or {}
        if token:hs['Authorization']='Bearer '+token
        if body is not None:hs['Content-Type']='application/json'
        req=Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=hs)
        return urlopen(req,timeout=30)
    def test_auth_and_list(self):
        with self.assertRaises(HTTPError) as err:self.request('/api/channels')
        self.assertEqual(401,err.exception.code)
        with self.assertRaises(HTTPError) as err:self.request('/api/login',{'password':'wrong'})
        self.assertEqual(401,err.exception.code)
        tok=json.load(self.request('/api/login',{'password':'very-long-test-password'}))['token']
        obj=json.load(self.request('/api/channels',token=tok))
        self.assertEqual(4,len(obj['channels']))
        self.assertIn('not browser',obj['recorder'])
    def test_sessions_endpoint_is_authenticated_and_fail_closed(self):
        with self.assertRaises(HTTPError) as err:self.request('/api/sessions')
        self.assertEqual(401,err.exception.code)
        tok=json.load(self.request('/api/login',{'password':'very-long-test-password'}))['token']
        result=json.load(self.request('/api/sessions',token=tok))
        self.assertEqual(result['state'],'local_windows')
        self.assertEqual([],result['sessions'])
    def test_seekable_playback_ticket(self):
        rid=self.engine.start('1',self.meta)['id']
        self.wait_for([rid])
        token=json.load(self.request('/api/login',{'password':'very-long-test-password'}))['token']
        ticket=json.load(self.request('/api/media-ticket',{'id':rid},token=token))['ticket']
        with self.assertRaises(HTTPError):self.request('/media/'+rid+'?ticket=bad')
        with self.request('/media/'+rid+'?ticket='+ticket,headers={'Range':'bytes=10-109'}) as response:
            self.assertEqual(206,response.status)
            self.assertEqual(100,len(response.read()))
            self.assertTrue(response.headers['Content-Range'].startswith('bytes 10-109/'))
        with self.request('/media/'+rid+'?ticket='+ticket) as response:
            self.assertEqual(200,response.status)
            self.assertEqual('video/mp4',response.headers['Content-Type'])

if __name__=='__main__':unittest.main()
