"""DocTutorials four-channel Windows/local recorder controller.

The web page is ONLY a control panel: browser permissions or screen capture are
never used. All media is captured by separately monitored FFmpeg workers.
Binds to 127.0.0.1, never expose this simple demo auth surface on the Internet.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time
from urllib.parse import urlsplit, parse_qs

from engine import Engine, RecorderError

STATIC=Path(__file__).parent/'web'
MAX_BODY=16384


def build_demo_config(root:Path):
    src={'kind':'lavfi','expression':'testsrc2=size=640x360:rate=15'}
    cam={'kind':'lavfi','expression':'testsrc2=size=320x180:rate=15'}
    audio={'kind':'lavfi','expression':'sine=frequency=440:sample_rate=48000'}
    return {'storage_root':str(root),'width':640,'height':360,'fps':15,'crf':25,
            'preset':'ultrafast','segment_seconds':20,
            'channels':{str(i):{'configured':True,'mode':'TEST MEDIA — NOT ZOOM',
                'screen':src,'faculty':cam,'audio':audio,'demo_duration_seconds':6} for i in range(1,5)}}


class ControlState:
    def __init__(self,engine,password):
        self.engine=engine
        self.password=password
        self.tokens={}
        self.media_tickets={}
        self.lock=threading.Lock()
    def login(self,password):
        if not hmac.compare_digest(password.encode('utf8'),self.password.encode('utf8')):
            return None
        token=secrets.token_urlsafe(36)
        with self.lock:
            now=time.monotonic()
            self.tokens={k:v for k,v in self.tokens.items() if v>now}
            self.tokens[token]=now+3600
        return token
    def authorized(self,header):
        if not header.startswith('Bearer '):return False
        token=header[7:]
        with self.lock:
            expiry=self.tokens.get(token,0)
        return expiry>time.monotonic()
    def issue_media_ticket(self,rid):
        token=secrets.token_urlsafe(36)
        with self.lock:
            now=time.monotonic()
            self.media_tickets={k:v for k,v in self.media_tickets.items() if v[1]>now}
            self.media_tickets[token]=(rid,now+3600)
        return token
    def verify_media_ticket(self,rid,ticket):
        with self.lock:
            item=self.media_tickets.get(ticket)
        return bool(item and item[0]==rid and item[1]>time.monotonic())
    def logout(self,header):
        with self.lock:self.tokens.pop(header.removeprefix('Bearer '),None)


def handler_factory(state):
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        server_version='DocTutorialsCentral/1.0'
        def log_message(self,fmt,*args):
            # No credential or session data in HTTP access log.
            pass
        def send(self,status,payload,content_type='application/json',extra=None):
            data=json.dumps(payload).encode('utf8') if content_type=='application/json' else payload
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            if extra:
                for k,v in extra.items():self.send_header(k,v)
            self.end_headers()
            self.wfile.write(data)
        def json_body(self):
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>MAX_BODY:raise RecorderError('Invalid request size.')
            obj=json.loads(self.rfile.read(length))
            if not isinstance(obj,dict):raise RecorderError('Expected a JSON object.')
            return obj
        def require(self):
            if not state.authorized(self.headers.get('Authorization','')):
                self.send(401,{'error':'Administrator login required.'})
                return False
            return True
        def do_GET(self):
            path=urlsplit(self.path).path
            if path in ('/','/app.js','/app.css','/logo.png'):
                mapping={'/':'index.html','/app.js':'app.js','/app.css':'app.css','/logo.png':'../assets/doctutorials-logo.png'}
                file=(STATIC/mapping[path]).resolve()
                mime='text/html; charset=utf-8' if path=='/' else ('text/javascript; charset=utf-8' if path.endswith('js') else ('text/css; charset=utf-8' if path.endswith('css') else 'image/png'))
                if not file.is_file():self.send(404,{'error':'Not found.'});return
                self.send(200,file.read_bytes(),mime)
                return
            media_match=re.fullmatch(r'/media/([0-9a-f]{32})',path)
            if media_match:
                params=parse_qs(urlsplit(self.path).query)
                ticket=params.get('ticket',[''])[0]
                if not state.verify_media_ticket(media_match.group(1),ticket):
                    self.send(401,{'error':'Invalid playback ticket.'});return
                try:self.serve_media(media_match.group(1),params.get('disposition',['play'])[0])
                except (RecorderError,ValueError,FileNotFoundError) as exc:self.send(400,{'error':str(exc)})
                return
            if not self.require():return
            try:
                if path=='/api/channels':
                    self.send(200,{'channels':state.engine.status(),'recorder':'FFmpeg native OS capture, not browser/Zoom local/cloud'})
                elif path=='/api/recordings':
                    self.send(200,{'recordings':state.engine.recordings()})
                else:
                    match=re.fullmatch(r'/api/recordings/([0-9a-f]{32})/(play|download)',path)
                    if match:
                        self.serve_media(*match.groups())
                    else:self.send(404,{'error':'Unknown endpoint.'})
            except (RecorderError,ValueError,FileNotFoundError) as exc:
                self.send(400,{'error':str(exc)})
        def serve_media(self,rid,disposition):
            path=state.engine.media_path(rid)
            total=path.stat().st_size
            start,end=0,total-1
            range_header=self.headers.get('Range','')
            if range_header:
                m=re.fullmatch(r'bytes=(\d*)-(\d*)',range_header)
                if not m:
                    self.send(416,{'error':'Invalid byte range.'});return
                if m.group(1):
                    start=int(m.group(1))
                    end=int(m.group(2)) if m.group(2) else end
                elif m.group(2):
                    start=max(0,total-int(m.group(2)))
                if start> end or start>=total:
                    self.send(416,{'error':'Requested range not available.'});return
                end=min(total-1,end)
            length=end-start+1
            self.send_response(206 if range_header else 200)
            self.send_header('Content-Type','video/mp4')
            self.send_header('Content-Length',str(length))
            self.send_header('Accept-Ranges','bytes')
            self.send_header('Cache-Control','private, no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('X-Content-Type-Options','nosniff')
            if range_header:self.send_header('Content-Range',f'bytes {start}-{end}/{total}')
            self.send_header('Content-Disposition',f'{"attachment" if disposition=="download" else "inline"}; filename="DocTutorials-{rid}.mp4"')
            self.end_headers()
            with path.open('rb') as fh:
                fh.seek(start)
                remaining=length
                while remaining:
                    data=fh.read(min(1024*1024,remaining))
                    if not data:break
                    try:self.wfile.write(data)
                    except (BrokenPipeError,ConnectionResetError):break
                    remaining-=len(data)
        def do_POST(self):
            path=urlsplit(self.path).path
            try:
                payload=self.json_body()
                if path=='/api/login':
                    token=state.login(str(payload.get('password','')))
                    if token:self.send(200,{'token':token,'expiresSeconds':3600})
                    else:self.send(401,{'error':'Invalid password.'})
                    return
                if not self.require():return
                if path=='/api/start':
                    channel=str(payload.get('channel',''))
                    meta={name:payload.get(name) for name in ('sessionId','course','subject','topic','faculty','facultyId')}
                    self.send(201,state.engine.start(channel,meta))
                elif path=='/api/stop':
                    self.send(200,{'recording':state.engine.stop(str(payload.get('channel','')))})
                elif path=='/api/recover':
                    self.send(200,{'recording':state.engine.recover(str(payload.get('id','')))})
                elif path=='/api/media-ticket':
                    rid=str(payload.get('id',''))
                    if not re.fullmatch(r'[0-9a-f]{32}',rid):raise RecorderError('Invalid recording ID.')
                    state.engine.media_path(rid)
                    self.send(200,{'ticket':state.issue_media_ticket(rid)})
                elif path=='/api/archive/retry':
                    rid=str(payload.get('id',''))
                    if not re.fullmatch(r'[0-9a-f]{32}',rid):raise RecorderError('Invalid recording ID.')
                    threading.Thread(target=state.engine.archive,args=(rid,),daemon=True).start()
                    self.send(202,{'archive':'started'})
                elif path=='/api/logout':
                    state.logout(self.headers.get('Authorization',''))
                    self.send(200,{'ok':True})
                else:self.send(404,{'error':'Unknown endpoint.'})
            except (ValueError,KeyError,RecorderError,json.JSONDecodeError) as exc:
                self.send(400,{'error':str(exc)})
            except Exception:
                self.send(500,{'error':'Unexpected recorder error; see server console.'})
    return Handler


def main(argv=None):
    ap=argparse.ArgumentParser(description='DocTutorials independent local four-channel recorder')
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--config',type=Path,help='Production input and NAS paths config (not Zoom SDK)')
    group.add_argument('--demo',action='store_true',help='Synthetic-media demonstration, NEVER Zoom capture')
    ap.add_argument('--port',type=int,default=8780)
    ap.add_argument('--storage-root',type=Path,default=Path.home()/'.config'/'doctutorials'/'central-demo-storage')
    args=ap.parse_args(argv)
    if args.demo:
        config=build_demo_config(args.storage_root)
    else:
        config=json.loads(args.config.read_text(encoding='utf8'))
        if not Path(config['storage_root']).is_absolute():
            raise SystemExit('storage_root must be an absolute Windows path in production config.')
    engine=Engine(config)
    password=os.getenv('DOCTUTORIALS_CONTROLLER_PASSWORD') or getpass.getpass('Choose central controller admin password (hidden, 12+ chars): ')
    if len(password)<12:raise SystemExit('Choose a password of at least 12 characters.')
    state=ControlState(engine,password)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_factory(state))
    print(f'DocTutorials Central Controller: http://127.0.0.1:{args.port}')
    print('Four independent worker slots. Storage: '+str(engine.root))
    print('Mode: '+('SYNTHETIC TEST MEDIA (not Zoom)' if args.demo else 'OPERATOR-CONFIGURED NATIVE INPUTS'))
    print('No OBS, Zoom Cloud Recording, or Zoom standard local recording used.')
    print('This service listens ONLY on 127.0.0.1. Keep this window open; Ctrl+C stops the UI.')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        print('Stopping active recorders and finalizing their files...')
        engine.close()
        print('Controller stopped. Check Storage Center for finalized recordings.')

if __name__=='__main__':main()
