"""RTMS protocol compatibility tests; no Zoom app/credits/media are assumed."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from controller import build_demo_config
from engine import Engine
from zoom_rtms_ingest import (ZoomRtmsReceiver, RtmsUnavailable, LiveStream,
                              select_zoom_wss, event_fields, RtmsTrackRecorder, signaling_handshake)


class EventCompatibilityTest(unittest.TestCase):
    def test_flat_and_nested_zoom_events(self):
        data={'meeting_uuid':'u','rtms_stream_id':'s',
              'meeting_id':123456789,'server_urls':'wss://a.zoom.us/socket'}
        self.assertEqual(event_fields(data)['meeting_id'],'123456789')
        self.assertEqual(event_fields({'object':data})['meeting_uuid'],'u')
        self.assertEqual(event_fields({'object':data})['rtms_stream_id'],'s')
        self.assertEqual(event_fields(None),{})

    def test_zoom_requires_initial_signaling_sequence_one(self):
        first=signaling_handshake('uuid','stream','client','SECRET')
        self.assertEqual(first['sequence'],1)
        self.assertEqual(first['protocol_version'],1)
        self.assertNotIn('SECRET',str(first))

    def test_endpoint_list_only_trusted_zoom(self):
        self.assertEqual(select_zoom_wss('wss://invalid.example/ws, wss://rtms.zoom.us/ok'),
                         'wss://rtms.zoom.us/ok')
        with self.assertRaises(RtmsUnavailable):
            select_zoom_wss('wss://attacker.test/token, wss://evil.zoom.us.attacker.test/ws')

    def test_flat_nested_events_start_stop_and_seq(self):
        with tempfile.TemporaryDirectory() as folder:
            engine=Engine(build_demo_config(Path(folder)/'engine'))
            now=2000
            assigned={'sessionId':'s1','facultyId':'f1','course':'NEET','subject':'Path',
                      'topic':'Test','startsAt':now-5,'endsAt':now+600,'plannedChannel':'1'}
            receiver=ZoomRtmsReceiver(engine,lambda:{'sessions':[assigned]},
                client_id='client',client_secret='secret',event_base='wss://events.zoom.us/events')
            event={'meeting_uuid':'uuid','rtms_stream_id':'stream',
                   'server_urls':'wss://bad.example/path, wss://rtms.zoom.us/path'}
            with mock.patch('zoom_rtms_ingest.time.time',return_value=now), \
                 mock.patch.object(receiver,'_connect_signal') as signal:
                receiver.handle_event('meeting.rtms_started',{'object':event})
                self.assertEqual(signal.call_count,1)
                self.assertEqual(signal.call_args.args[1],'wss://rtms.zoom.us/path')
                self.assertEqual(receiver.state()['streamRequests'],1)
                with mock.patch.object(receiver,'_stop_media') as stop:
                    receiver.handle_event('meeting.rtms_stopped',{'object':{'rtms_stream_id':'stream'}})
                    stop.assert_called_once_with(None,'stream')
            receiver.close();engine.close()

    def test_ack_only_once_after_all_three_media_handshakes(self):
        with tempfile.TemporaryDirectory() as folder:
            engine=Engine(build_demo_config(Path(folder)/'engine'))
            receiver=ZoomRtmsReceiver(engine,lambda:{'sessions':[]},
                client_id='client',client_secret='secret',event_base='wss://events.zoom.us/events')
            capture=RtmsTrackRecorder(engine.root/'staging'/'test',
                {'sessionId':'s1','facultyId':'f1','course':'c','subject':'s','topic':'t'},'1')
            socket=mock.Mock()
            record=LiveStream('stream','uuid',{},capture,signaling=socket,media={})
            receiver.live['stream']=record
            receiver.media_ready(record,'audio')
            receiver.media_ready(record,'faculty')
            socket.send.assert_not_called()
            receiver.media_ready(record,'screen')
            receiver.media_ready(record,'screen')
            socket.send.assert_called_once()
            self.assertEqual(socket.send.call_args.args[0],'{"msg_type": 7, "rtms_stream_id": "stream"}')
            receiver.close();engine.close()


if __name__=='__main__':unittest.main()
