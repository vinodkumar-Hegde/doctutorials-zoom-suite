"""Read-only, operator-paired HTTPS LAN bridge for the Mac Admin session database.

Run on the Mac containing the DocTutorials Live HTTPS demo. Never exposes meeting
numbers, passcodes, SDK tokens or passwords; it serves only seven scheduling fields.
The existing 127.0.0.1:8443 backend remains unchanged and can keep running.
"""
from __future__ import annotations

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import getpass
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import ssl
import sys

FIELDS=('sessionId','facultyId','course','subject','topic','startsAt','endsAt')


def read_public_sessions(db_path:Path):
    if not db_path.is_file() or db_path.is_symlink():
        return []
    uri=db_path.resolve().as_uri()+'?mode=ro'
    with sqlite3.connect(uri,uri=True,timeout=3) as db:
        rows=db.execute('''SELECT session_id, faculty_id, course, subject, topic, starts_at, ends_at
            FROM sessions ORDER BY starts_at, session_id LIMIT 500''').fetchall()
    return [dict(zip(FIELDS,row)) for row in rows]


def make_handler(db_path:Path, token:str):
    class Handler(BaseHTTPRequestHandler):
        server_version='DocTutorials-ReadOnly-Sessions'
        protocol_version='HTTP/1.1'
        def log_message(self,fmt,*args):
            pass # do not log authentication or private sessions
        def send_json(self,status:int, data):
            body=json.dumps(data,separators=(',',':')).encode('utf8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            if self.path!='/api/recorder/sessions':
                self.send_json(404,{'error':'Not found'});return
            header=self.headers.get('Authorization','')
            if not hmac.compare_digest(header.encode('utf8'),('Bearer '+token).encode('utf8')):
                self.send_json(401,{'error':'Authorization required'});return
            try:
                self.send_json(200,{'sessions':read_public_sessions(db_path)})
            except sqlite3.Error:
                self.send_json(503,{'error':'Admin database unavailable'})
        def do_POST(self):
            self.send_json(405,{'error':'Read only'})
    return Handler


class QuietSessionServer(ThreadingHTTPServer):
    def handle_error(self,request,client_address):
        exc=sys.exc_info()[1]
        if isinstance(exc,(BrokenPipeError,ConnectionResetError,ssl.SSLError)):
            return # Certificate mismatch clients close before sending an HTTP request
        super().handle_error(request,client_address)


def main(argv=None):
    ap=argparse.ArgumentParser(description='DocTutorials Mac read-only HTTPS session schedule bridge')
    home=Path.home()/'.config'/'doctutorials'
    ap.add_argument('--database',type=Path,default=home/'demo-live-sessions.sqlite3')
    ap.add_argument('--cert',type=Path,default=home/'localhost-tls'/'localhost.pem')
    ap.add_argument('--key',type=Path,default=home/'localhost-tls'/'localhost.key')
    ap.add_argument('--port',type=int,default=8444)
    ap.add_argument('--bind',default='0.0.0.0')
    args=ap.parse_args(argv)
    if not args.cert.is_file() or not args.key.is_file():
        raise SystemExit('Mac HTTPS demo certificate missing. Keep the existing certificate; do not regenerate SDK secrets.')
    token=getpass.getpass('Session bridge pairing secret (hidden, at least 20 characters): ')
    if len(token)<20 or len(token)>256 or '\n' in token or '\r' in token:
        raise SystemExit('Use a unique secret of 20-256 characters; do not share it in chat.')
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version=ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(args.cert),str(args.key))
    der=ssl.PEM_cert_to_DER_cert(args.cert.read_text(encoding='ascii'))
    digest=hashlib.sha256(der).hexdigest()
    server=QuietSessionServer((args.bind,args.port),make_handler(args.database,token))
    server.socket=context.wrap_socket(server.socket,server_side=True)
    print('DocTutorials session bridge running on Mac port',args.port)
    print('Certificate SHA256:',digest)
    print('Reads only schedule metadata; no Zoom credentials or passcodes.')
    print('Keep this Mac window open. Allow incoming traffic only from the recording PC.')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
