"""Offline RTMS transport/packet composition checks; NOT Zoom acceptance."""
from __future__ import annotations
import base64
from pathlib import Path
import subprocess
import tempfile
import unittest
import time
from unittest import mock

from controller import build_demo_config
from engine import Engine
from zoom_rtms_ingest import (RtmsTrackRecorder,RtmsUnavailable,ZoomRtmsReceiver,
    media_handshake,rtms_signature,trusted_wss,unique_active_assignment)

ASSIGNED={'sessionId':'class001','facultyId':'testfac','course':'NEET SS',
          'subject':'Pathology','topic':'Test','startsAt':1000,'endsAt':4000,
          'plannedChannel':'1'}


def encode_packet(msg_type, raw, when, user='0'):
    return {'msg_type':msg_type,'content':{'data':base64.b64encode(raw).decode(),
            'timestamp':when,'user_id':user}}


class ProtocolTest(unittest.TestCase):
    def test_zoom_tls_only_no_ssrf(self):
        for host in ['ws://rtms.zoom.us/x','wss://zoom.us.evil.com/a',
                     'wss://localhost/x','file:///etc/passwd','wss://user@rtms.zoom.us/x',
                     'wss://rtms.zoom.us:9999/x']:
            with self.subTest(host=host),self.assertRaises(RtmsUnavailable):trusted_wss(host)
        self.assertEqual(trusted_wss('wss://abc.zoom.us/socket'),'wss://abc.zoom.us/socket')

    def test_unique_active_schedule_only(self):
        item=unique_active_assignment({'sessions':[ASSIGNED]},now=2000)
        self.assertEqual(item['plannedChannel'],'1')
        with self.assertRaises(RtmsUnavailable):unique_active_assignment({'sessions':[ASSIGNED,ASSIGNED]},now=2000)
        with self.assertRaises(RtmsUnavailable):unique_active_assignment({'sessions':[ASSIGNED]},now=5000)

    def test_handshake_does_not_expose_secret(self):
        handshake=media_handshake('screen','uuid','stream','client','secret')
        self.assertEqual(handshake['msg_type'],3)
        self.assertEqual(handshake['media_type'],4)
        self.assertEqual(handshake['media_params']['deskshare']['codec'],7)
        self.assertEqual(len(rtms_signature('client','secret','uuid','stream')),64)
        self.assertNotIn('secret',str(handshake))

    def test_receiver_does_not_claim_capture_before_packets(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(build_demo_config(Path(d)/'engine'))
            r=ZoomRtmsReceiver(engine,lambda:{'sessions':[{
                  **ASSIGNED,'startsAt':int(time.time())-60,'endsAt':int(time.time())+600}]},
                  client_id='id',client_secret='secret',event_base='wss://a.zoom.us/evt')
            with mock.patch.object(r,'_connect_signal'):
                r.handle_event('meeting.rtms_started',{
                    'meeting_uuid':'u','rtms_stream_id':'stream1','server_urls':'wss://a.zoom.us/ws'})
                self.assertEqual(r.state()['streamRequests'],1)
                self.assertEqual(r.state()['observedMediaChannels'],[])
            r.close();engine.close()

    def test_packet_validation(self):
        with tempfile.TemporaryDirectory() as d:
            writer=RtmsTrackRecorder(Path(d)/'track',ASSIGNED,'1')
            self.assertFalse(writer.ingest(encode_packet(14,b'\x00\x00',1000,user='45')))
            self.assertFalse(writer.ingest(encode_packet(15,b'noth264',1000)))
            self.assertFalse(writer.ingest(encode_packet(16,b'\x00\x00\x00\x01xyz',-1)))
            self.assertTrue(writer.ingest(encode_packet(16,b'\x00\x00\x00\x01xyz',1000)))
            self.assertFalse(writer.ingest(encode_packet(16,b'\x00\x00\x00\x01xyz',900)))
            writer.close()
            self.assertEqual(writer.sizes['screen'],7)

    def test_missing_media_is_preserved_not_cataloged(self):
        with tempfile.TemporaryDirectory() as d:
            engine=Engine(build_demo_config(Path(d)/'engine'))
            writer=RtmsTrackRecorder(engine.root/'staging'/'rtms_missing',ASSIGNED,'1')
            writer.ingest(encode_packet(14,b'\x00\x00',1000))
            with self.assertRaises(RtmsUnavailable):writer.compose(engine)
            self.assertTrue((writer.root/'audio.s16le').exists())
            self.assertEqual(engine.recordings(),[])
            engine.close()

    def test_real_ffmpeg_packet_mux_and_storage(self):
        """FFmpeg-generated synthetic H264/PCM frames wrapped in RTMS JSON packets.

        Tests actual compositor+MP4+catalog but NOT any Zoom network media.
        """
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            engine=Engine(build_demo_config(root/'engine'))
            writer=RtmsTrackRecorder(engine.root/'staging'/'rtms_fixture',ASSIGNED,'1')
            share=root/'share.h264';face=root/'face.h264';audio=root/'audio.raw'
            for path,kind in [(share,'testsrc2=size=320x180:rate=25'),(face,'testsrc=size=160x90:rate=25')]:
                subprocess.run([engine.ffmpeg,'-loglevel','error','-y','-f','lavfi','-i',kind,
                    '-t','1.2','-c:v','libx264','-preset','ultrafast','-f','h264',str(path)],check=True,timeout=30)
            subprocess.run([engine.ffmpeg,'-loglevel','error','-y','-f','lavfi','-i','sine=frequency=420:sample_rate=16000',
                '-t','1.2','-f','s16le',str(audio)],check=True,timeout=30)
            for packet_type,path in [(15,face),(16,share)]:
                raw=path.read_bytes()
                # Split on Annex-B boundaries to avoid truncating a NAL unit.
                positions=[]
                for i in range(len(raw)-4):
                    if raw[i:i+4]==b'\x00\x00\x00\x01':positions.append(i)
                self.assertGreater(len(positions),3)
                starts=[0]+[positions[(len(positions)*k)//3] for k in (1,2)]+[len(raw)]
                for k in range(3):
                    self.assertTrue(writer.ingest(encode_packet(packet_type,raw[starts[k]:starts[k+1]],1000+40*k)))
            data=audio.read_bytes()
            each=(len(data)//6)*2
            for k in range(3):
                self.assertTrue(writer.ingest(encode_packet(14,data[k*each:(k+1)*each] if k<2 else data[k*each:],1000+k*400)))
            result=writer.compose(engine)
            self.assertEqual(result['state'],'ready')
            self.assertEqual(result['channel'],'1')
            self.assertEqual(engine.recordings()[0]['course'],'NEET SS')
            self.assertGreater(engine.media_path(result['id']).stat().st_size,4000)
            engine.close()

if __name__=='__main__':unittest.main()
