import importlib, os, sqlite3, sys, tempfile, types, unittest, threading, time
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auto_zoom_events as m

class AutoTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
  self.db=Path(self.temp.name)/'private.sqlite3'; self.item={'sessionId':'class001','facultyId':'fac1','course':'Course','subject':'Subject','topic':'Topic','startsAt':int(time.time())-30,'endsAt':int(time.time())+900,'plannedChannel':'1'}
  with sqlite3.connect(self.db) as db:
   db.execute('CREATE TABLE sessions(session_id TEXT, faculty_id TEXT, course TEXT, subject TEXT, topic TEXT, meeting_id TEXT)')
   db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',('class001','fac1','Course','Subject','Topic','12345678901'))
  self.desktop=Mock();self.desktop.private_db=self.db;self.desktop.finder.return_value=[]
  self.engine=Mock();self.engine.processes={}
  self.plan=lambda: {'sessions':[self.item]}
  self.body={'payload':{'object':{'id':'12345678901','uuid':'meetinginstance'}}}
 def test_match_exact_id(self):
  self.assertEqual(m.match_zoom_meeting(self.db,self.plan(),'12345678901')['sessionId'],'class001')
  with self.assertRaises(m.ZoomAutoUnavailable):m.match_zoom_meeting(self.db,self.plan(),'12345678902')
  with self.assertRaises(m.ZoomAutoUnavailable):m.match_zoom_meeting(self.db,{'sessions':[]},'12345678901')
  with self.assertRaises(m.ZoomAutoUnavailable):m.match_zoom_meeting(self.db,{'sessions':[self.item,self.item]},'12345678901')
 def test_s2s_token_uses_account_credentials(self):
  import json
  listener=m.ZoomMeetingEventListener(Mock(),client_id='client-id',client_secret='client-secret',
      account_id='account-id',event_wss='wss://ws.zoom.us/ws?subscriptionId=abc')
  response=Mock()
  response.read.return_value=json.dumps({'access_token':'not-a-real-token'}).encode()
  cm=Mock()
  cm.__enter__=Mock(return_value=response)
  cm.__exit__=Mock(return_value=False)
  with patch('auto_zoom_events.urlopen',return_value=cm) as call:
   self.assertEqual(listener._token(),'not-a-real-token')
  req=call.call_args.args[0]
  self.assertEqual(req.get_method(),'POST')
  self.assertEqual(req.full_url,'https://zoom.us/oauth/token')
  self.assertEqual(parse_qs(req.data.decode()),{'grant_type':['account_credentials'],'account_id':['account-id']})
  self.assertEqual(req.get_header('Authorization'),'Basic Y2xpZW50LWlkOmNsaWVudC1zZWNyZXQ=')
 def test_s2s_missing_account_id_rejected(self):
  with self.assertRaises(m.ZoomAutoUnavailable):
   m.ZoomMeetingEventListener(Mock(),client_id='id',client_secret='secret',
      account_id='',event_wss='wss://ws.zoom.us/ws?subscriptionId=abc')
 def test_event_url_security(self):
  self.assertEqual(m.zoom_event_wss('wss://ws.zoom.us/ws?subscriptionId=abc'), 'wss://ws.zoom.us/ws?subscriptionId=abc')
  for url in ('ws://ws.zoom.us/','wss://ws.zoom.us.evil.com/a','wss://localhost','wss://user@zoom.us','wss://ws.zoom.us:1234'):
   with self.assertRaises(m.ZoomAutoUnavailable): m.zoom_event_wss(url)
 def test_event_start_without_notice_rejected(self):
  auto=m.AutoDesktopRecorder(self.engine,self.desktop,self.plan,notice_approved=False)
  self.assertFalse(auto.handle_event('meeting.started',self.body));self.desktop.open.assert_not_called()
 def test_event_start_and_auto_capture(self):
  entered=threading.Event()
  def capture(*args):entered.set()
  self.desktop.finder.side_effect=[[],[object()]]
  self.desktop.start_capture.side_effect=capture
  auto=m.AutoDesktopRecorder(self.engine,self.desktop,self.plan,notice_approved=True, poll_seconds=.001)
  self.assertTrue(auto.handle_event('meeting.started',self.body))
  self.assertTrue(entered.wait(1))
  self.assertFalse(auto.handle_event('meeting.started',self.body))
  self.assertEqual(auto.status()['phase'],'capture_started_unverified')
  self.assertTrue(auto.handle_event('meeting.ended',self.body))
  deadline=time.time()+2
  while time.time()<deadline and auto.status()['phase']!='saved_to_storage_center':time.sleep(.01)
  self.engine.stop.assert_called_once_with('1')
 def test_unmatched_event_never_launches(self):
  auto=m.AutoDesktopRecorder(self.engine,self.desktop,self.plan,notice_approved=True)
  bad={'payload':{'object':{'id':'98765432100','uuid':'meetinginstance'}}}
  self.assertFalse(auto.handle_event('meeting.started',bad));self.desktop.open.assert_not_called()
 def test_preexisting_meeting_fail_closed(self):
  self.desktop.finder.return_value=[object()]
  auto=m.AutoDesktopRecorder(self.engine,self.desktop,self.plan,notice_approved=True)
  self.assertFalse(auto.handle_event('meeting.started',self.body));self.desktop.open.assert_not_called()
if __name__=='__main__':unittest.main()