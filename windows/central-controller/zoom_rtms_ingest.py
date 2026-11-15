"""Experimental native RTMS media ingress for Windows (outbound WebSockets only).

No Zoom client, browser/OBS capture, Zoom Cloud Recording, or fake media.
Not production-proven: network reconnect, frame jitter / timestamps, individual
faculty mapping and four simultaneous real streams require acceptance tests.

Requires an *separately authorized* RTMS app and Zoom Developer Pack credits.
No app secrets are stored, and no meeting IDs/URLs are returned to browser.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit
from urllib.request import Request, urlopen
from dataclasses import dataclass

from engine import RecorderError, make_overlay

_ALLOWED_HOSTS = ('.zoom.us', '.zoom.com')
_STREAM_ID = re.compile(r'^[a-zA-Z0-9_-]{1,256}$')
_MAX_ENCODED = 4_000_000
_PACKET_TYPES = {14:'audio', 15:'faculty', 16:'screen'}
_MEDIA_FLAGS = {'audio':1,'faculty':2,'screen':4}
_MEDIA_KEYS = {'audio':'audio','faculty':'video','screen':'deskshare'}


class RtmsUnavailable(RecorderError):
    """RTMS authorization, connection, or track data isn't available."""


def trusted_wss(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise RtmsUnavailable('Invalid RTMS endpoint.')
    parsed = urlsplit(value)
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'wss' or not any(host.endswith(suffix) for suffix in _ALLOWED_HOSTS):
        raise RtmsUnavailable('RTMS endpoint must be a Zoom wss:// host.')
    if parsed.username or parsed.password or parsed.fragment or parsed.port not in (None,443):
        raise RtmsUnavailable('Invalid RTMS endpoint authority.')
    return value


def rtms_signature(client_id: str, secret: str, meeting_uuid: str, stream_id: str) -> str:
    if not all(isinstance(v,str) and v for v in (client_id,secret,meeting_uuid,stream_id)):
        raise RtmsUnavailable('RTMS app credentials or stream identity missing.')
    return hmac.new(secret.encode('utf8'),
                    f'{client_id},{meeting_uuid},{stream_id}'.encode('utf8'),
                    hashlib.sha256).hexdigest()


def unique_active_assignment(snapshot: dict, *, now: int | None = None):
    """Never guess across multiple overlapping classes: no cross-class recordings."""
    now = int(time.time()) if now is None else int(now)
    items = [s for s in snapshot.get('sessions',[]) if s.get('plannedChannel') in {'1','2','3','4'}
             and s.get('startsAt',10**20) <= now < s.get('endsAt',0)]
    if len(items) != 1:
        raise RtmsUnavailable('Cannot uniquely match RTMS stream to an assigned class; Zoom-to-class identity mapping required.')
    return dict(items[0])


def media_handshake(media_kind: str, meeting_uuid: str, stream_id: str, client_id: str, secret: str):
    if media_kind == 'audio':
        params = {'content_type':2,'sample_rate':1,'channel':1,'codec':1,'data_opt':1,'send_rate':100}
    else:
        params = {'content_type':3,'codec':7,'resolution':2,'fps':25}
    key = _MEDIA_KEYS[media_kind]
    return {'msg_type':3,'protocol_version':1,'meeting_uuid':meeting_uuid,
            'rtms_stream_id':stream_id,
            'signature':rtms_signature(client_id,secret,meeting_uuid,stream_id),
            'media_type':_MEDIA_FLAGS[media_kind], 'payload_encryption':False,
            'media_params':{key:params}}


class RtmsTrackRecorder:
    """Durably store real RTMS media packets and compose a post-meeting MP4.

    H.264 tracks need valid Annex B frames; audio needs mixed speaker ID=0.
    This is a controlled *first meeting* media proof; timestamps are retained
    as evidence but full jitter/gap synchronization is NOT implemented.
    """
    def __init__(self, root:Path, assignment:dict, channel:str):
        self.assignment=dict(assignment)
        self.channel=str(channel)
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=False)
        self.lock=threading.RLock()
        self.handles={kind:(self.root/filename).open('xb') for kind,filename in
                      (('audio','audio.s16le'),('faculty','faculty.h264'),('screen','screen.h264'))}
        self.counts={k:0 for k in self.handles}
        self.sizes={k:0 for k in self.handles}
        self.first_timestamp={k:None for k in self.handles}
        self.last_timestamp={k:None for k in self.handles}
        self.closed=False
        self.errors=[]

    def ingest(self, packet:dict) -> bool:
        kind=_PACKET_TYPES.get(packet.get('msg_type')) if isinstance(packet,dict) else None
        if kind is None: return False
        content=packet.get('content')
        if not isinstance(content,dict): return False
        if kind=='audio' and str(content.get('user_id'))!='0':
            return False  # Prevent mixing individual and mixed packets.
        encoded=content.get('data')
        if not isinstance(encoded,str) or len(encoded)>_MAX_ENCODED:
            return False
        try: raw=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error): return False
        if not raw or len(raw)>3_000_000: return False
        if kind!='audio' and not (raw.startswith(b'\x00\x00\x00\x01') or raw.startswith(b'\x00\x00\x01')):
            return False  # Unknown format/codec; don't pass as H.264.
        if kind=='audio' and len(raw)%2: return False
        stamp=content.get('timestamp')
        if isinstance(stamp,bool) or not isinstance(stamp,int) or stamp<0:
            return False
        with self.lock:
            if self.closed: return False
            if self.last_timestamp[kind] is not None and stamp < self.last_timestamp[kind]:
                return False  # Drop duplicate/late packets rather than rewind.
            self.handles[kind].write(raw)
            self.counts[kind]+=1
            self.sizes[kind]+=len(raw)
            if self.first_timestamp[kind] is None:self.first_timestamp[kind]=stamp
            self.last_timestamp[kind]=stamp
        return True

    def close(self):
        with self.lock:
            if self.closed:return
            self.closed=True
            for h in self.handles.values():
                h.flush()
                os.fsync(h.fileno())
                h.close()
            # These are anonymized stream timing metrics, not participant identities.
            (self.root/'timing.json').write_text(json.dumps({
                k:{'packets':self.counts[k],'bytes':self.sizes[k],
                   'first_ms':self.first_timestamp[k],
                   'last_ms':self.last_timestamp[k]}
                for k in self.counts},indent=2),encoding='utf8')

    def compose(self, engine):
        self.close()
        if not all(self.sizes[k]>0 for k in ('audio','faculty','screen')):
            raise RtmsUnavailable('RTMS recording incomplete: teaching screen, active-speaker video and mixed audio are all required.')
        if any(self.counts[k]<3 for k in ('audio','faculty','screen')):
            raise RtmsUnavailable('RTMS recording has too few real media packets to produce a verified class video.')
        a=self.assignment
        meta={'sessionId':a['sessionId'],'facultyId':a['facultyId'],
              'faculty':a['facultyId'],'course':a['course'],
              'subject':a['subject'],'topic':a['topic']}
        width=int(engine.config.get('width',1920));height=int(engine.config.get('height',1080))
        fps=25
        camw=(width*23//100)//2*2
        camh=(camw*9//16)//2*2
        cam={'x':width-camw-max(12,width//50), 'y':max(12,width//50),
             'width':camw,'height':camh}
        make_overlay(self.root/'overlay.png',engine.logo,meta,width,height,cam)
        output=self.root/'composed.mp4'
        # Timestamp sidecars are retained. Full stream gap filling and A/V drift
        # repair are NOT implemented; assess actual timing before production.
        filters=(
            f'[0:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,'
            f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[screen];'
            f'[1:v]fps={fps},scale={camw}:{camh}:force_original_aspect_ratio=decrease,'
            f'pad={camw}:{camh}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[faculty];'
            f'[screen][faculty]overlay={cam["x"]}:{cam["y"]}:shortest=1[composed];'
            f'[composed][3:v]overlay=0:0:format=auto,format=yuv420p[out]'
        )
        cmd=[engine.ffmpeg,'-hide_banner','-loglevel','error','-y',
             '-fflags','+genpts','-r',str(fps),'-f','h264','-i',str(self.root/'screen.h264'),
             '-fflags','+genpts','-r',str(fps),'-f','h264','-i',str(self.root/'faculty.h264'),
             '-f','s16le','-ar','16000','-ac','1','-i',str(self.root/'audio.s16le'),
             '-loop','1','-framerate',str(fps),'-i',str(self.root/'overlay.png'),
             '-filter_complex',filters,'-map','[out]','-map','2:a:0',
             '-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',
             '-c:a','aac','-ar','48000','-ac','2','-b:a','128k','-shortest',
             '-movflags','+faststart',str(output)]
        try:
            proc=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                                timeout=180,text=True)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise RtmsUnavailable('FFmpeg RTMS composition failed; original media tracks are preserved.') from exc
        if proc.returncode or not output.exists():
            raise RtmsUnavailable('FFmpeg could not compose these RTMS media tracks; original tracks preserved.')
        return engine.import_verified_mp4(self.channel,meta,output,source='zoom_rtms')


@dataclass
class LiveStream:
    stream_id:str
    meeting_uuid:str
    assignment:dict
    capture:RtmsTrackRecorder
    signaling:object|None=None
    media:dict|None=None


class ZoomRtmsReceiver:
    """Connects from Windows outbound to authorized Zoom Event WebSocket.

    No inbound listener/public port. Not started unless --rtms and env configured.
    Only one uniquely active assignment can be correlated with no meeting IDs.
    """
    def __init__(self,engine,plan_callback,*,client_id:str,client_secret:str,event_base:str):
        if not client_id or not client_secret or not event_base:
            raise RtmsUnavailable('RTMS app credentials/Event WebSocket URL missing.')
        self.engine=engine
        self.plan=plan_callback
        self.client_id=client_id
        self.secret=client_secret
        self.event_base=trusted_wss(event_base)
        self.lock=threading.RLock()
        self.live={}
        self.errors=[]
        self._event_socket=None
        self._thread=None
        self._closing=False

    def state(self):
        with self.lock:
            return {'enabled':True,'streamRequests':len(self.live),
                    'observedMediaChannels':[s.capture.channel for s in self.live.values()
                        if all(s.capture.sizes[k]>0 for k in ('screen','faculty','audio'))]}

    def oauth_token(self):
        import base64 as b64
        basic=b64.b64encode(f'{self.client_id}:{self.secret}'.encode()).decode()
        req=Request('https://zoom.us/oauth/token?grant_type=client_credentials',
                    method='POST',headers={'Authorization':'Basic '+basic})
        with urlopen(req,timeout=20) as response:
            payload=json.loads(response.read(100000))
        token=payload.get('access_token')
        if not isinstance(token,str) or not token:
            raise RtmsUnavailable('Zoom Event WebSocket OAuth authorization failed.')
        return token

    def start(self):
        if self._thread:return
        self._thread=threading.Thread(target=self._run_events,daemon=True,name='doctutorials-rtms-events')
        self._thread.start()

    def _run_events(self):
        import websocket
        retries=0
        while not self._closing:
            try:
                token=self.oauth_token()
                base=urlsplit(self.event_base)
                query=dict(parse_qsl(base.query,keep_blank_values=True))
                query['access_token']=token
                url=urlunsplit((base.scheme,base.netloc,base.path,urlencode(query),'') )
                def opened(ws):
                    nonlocal retries
                    retries=0
                    ws.send(json.dumps({'module':'heartbeat'}))
                    def beat():
                        while not self._closing and ws.sock and ws.sock.connected:
                            time.sleep(30)
                            try:ws.send(json.dumps({'module':'heartbeat'}))
                            except (OSError,websocket.WebSocketException):break
                    threading.Thread(target=beat,daemon=True).start()
                def received(ws,message):
                    try:
                        data=json.loads(message)
                        if data.get('module')!='message':return
                        body=json.loads(data.get('content','{}'))
                        self.handle_event(body.get('event'),body.get('payload'))
                    except (ValueError,TypeError,RtmsUnavailable):
                        pass # No raw Zoom event payloads in logs.
                self._event_socket=websocket.WebSocketApp(url,on_open=opened,on_message=received)
                self._event_socket.run_forever(ping_interval=25,ping_timeout=10)
            except (OSError,ValueError,KeyError,ImportError,RtmsUnavailable):
                pass
            if self._closing:break
            retries=min(retries+1,5)
            time.sleep(min(30,2**retries))

    def handle_event(self,event:str,payload:dict):
        if event=='meeting.rtms_started':
            self._start_media(payload)
        elif event=='meeting.rtms_stopped':
            uuid_value=payload.get('meeting_uuid') if isinstance(payload,dict) else None
            if isinstance(uuid_value,str):self._stop_media(uuid_value)

    def _start_media(self,payload):
        if not isinstance(payload,dict):return
        uuid_value,stream_id,url=(payload.get(k) for k in ('meeting_uuid','rtms_stream_id','server_urls'))
        if not isinstance(uuid_value,str) or not uuid_value or len(uuid_value)>256 or not isinstance(stream_id,str) or not _STREAM_ID.fullmatch(stream_id):
            return
        try:
            trusted_wss(url)
            assignment=unique_active_assignment(self.plan())
        except RtmsUnavailable:
            return
        channel=assignment['plannedChannel']
        with self.lock:
            if stream_id in self.live or any(s.capture.channel==channel for s in self.live.values()):return
            if channel in self.engine.processes and self.engine.processes[channel].poll() is None:return
            staging=self.engine.root/'staging'/('rtms_'+hashlib.sha256(stream_id.encode()).hexdigest()[:24])
            if staging.exists():return
            capture=RtmsTrackRecorder(staging,assignment,channel)
            record=LiveStream(stream_id,uuid_value,assignment,capture,media={})
            self.live[stream_id]=record
        try:
            self._connect_signal(record,url)
        except (ImportError,OSError,ValueError):
            capture.close()
            with self.lock:self.live.pop(stream_id,None)

    def _connect_signal(self,record,url):
        import websocket
        def on_open(ws):
            ws.send(json.dumps({'msg_type':1,'protocol_version':1,
                'meeting_uuid':record.meeting_uuid,'rtms_stream_id':record.stream_id,
                'sequence':random.SystemRandom().randint(1,10**9),
                'signature':rtms_signature(self.client_id,self.secret,record.meeting_uuid,record.stream_id),
                'buffer_data':False}))
        def on_msg(ws,message):
            try:
                msg=json.loads(message)
                if msg.get('msg_type')==2 and msg.get('status_code')==0:
                    urls=msg.get('media_server',{}).get('server_urls',{})
                    for kind,key in _MEDIA_KEYS.items():
                        endpoint=urls.get(key)
                        if endpoint:self._connect_media(record,kind,trusted_wss(endpoint))
                elif msg.get('msg_type')==12:
                    ws.send(json.dumps({'msg_type':13,'timestamp':msg['timestamp']}))
            except (ValueError,KeyError,TypeError,RtmsUnavailable):pass
        sock=websocket.WebSocketApp(url,on_open=on_open,on_message=on_msg)
        record.signaling=sock
        threading.Thread(target=sock.run_forever,daemon=True).start()

    def _connect_media(self,record,kind,url):
        import websocket
        if kind in record.media:return
        def on_open(ws):
            ws.send(json.dumps(media_handshake(kind,record.meeting_uuid,record.stream_id,self.client_id,self.secret)))
        def on_msg(ws,message):
            try:
                msg=json.loads(message)
                if msg.get('msg_type')==4 and msg.get('status_code')==0:
                    if record.signaling:
                        record.signaling.send(json.dumps({'msg_type':7,'rtms_stream_id':record.stream_id}))
                elif msg.get('msg_type')==12:
                    ws.send(json.dumps({'msg_type':13,'timestamp':msg['timestamp']}))
                elif msg.get('msg_type') in _PACKET_TYPES:
                    expected=_PACKET_TYPES[msg['msg_type']]
                    if expected==kind:record.capture.ingest(msg)
            except (ValueError,TypeError,KeyError,OSError):pass
        sock=websocket.WebSocketApp(url,on_open=on_open,on_message=on_msg)
        record.media[kind]=sock
        threading.Thread(target=sock.run_forever,daemon=True).start()

    def _stop_media(self,meeting_uuid):
        with self.lock:
            matched=[(sid,rec) for sid,rec in self.live.items() if rec.meeting_uuid==meeting_uuid]
            for sid,_ in matched:self.live.pop(sid,None)
        for _,record in matched:
            for sock in [record.signaling,*record.media.values()]:
                if sock:
                    try:sock.close()
                    except (OSError,ValueError):pass
            def finish(rec):
                # Give in-flight media packet callbacks a short time to exit.
                time.sleep(.3)
                try:rec.capture.compose(self.engine)
                except (RecorderError,ValueError,OSError):
                    rec.capture.close() # staged media preserved for analysis/recovery
            threading.Thread(target=finish,args=(record,),daemon=True).start()

    def close(self):
        self._closing=True
        if self._event_socket:self._event_socket.close()
        with self.lock:
            active=list(self.live.values())
            self.live.clear()
        for rec in active:
            for s in [rec.signaling,*rec.media.values()]:
                if s:
                    try:s.close()
                    except (OSError,ValueError):pass
            rec.capture.close()  # On service restart preserve, never mislabel as complete.
