"""Read-only, TLS-certificate-pinned DocTutorials Admin session schedule client.

The Windows controller never receives Zoom meeting IDs, passcodes, JWTs or SDK credentials.
The operator must explicitly pair this client to their Mac bridge. No TLS trust-on-first-use.
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import ipaddress
import json
from pathlib import Path
import re
import ssl
import threading
import time
from urllib.parse import urlsplit

class FeedError(RuntimeError):
    pass

FIELDS=('sessionId','facultyId','course','subject','topic','startsAt','endsAt')
_ID=re.compile(r'^[A-Za-z0-9_-]{1,64}$')
_FP=re.compile(r'^[0-9a-f]{64}$')


def validate_public_sessions(body):
    if not isinstance(body,dict) or not isinstance(body.get('sessions'),list) or len(body['sessions'])>500:
        raise FeedError('Session feed returned an invalid response.')
    clean=[]
    for item in body['sessions']:
        if not isinstance(item,dict) or set(item)!=set(FIELDS):
            raise FeedError('Session feed contains unexpected fields.')
        if not (_ID.fullmatch(str(item['sessionId'])) and _ID.fullmatch(str(item['facultyId']))):
            raise FeedError('Session feed contains an invalid identifier.')
        if not all(isinstance(item[k],str) and 0<len(item[k])<=180 and not any(ord(c)<32 for c in item[k])
                   for k in ('course','subject','topic')):
            raise FeedError('Session feed contains invalid display text.')
        if not all(isinstance(item[k],int) and not isinstance(item[k],bool) for k in ('startsAt','endsAt')):
            raise FeedError('Session feed contains an invalid time.')
        if not (1_600_000_000<=item['startsAt']<item['endsAt']<=4_102_444_800):
            raise FeedError('Session feed contains an invalid schedule.')
        clean.append({k:item[k] for k in FIELDS})
    return clean


def fetch_pinned_sessions(config:dict, *, timeout:float=5.0):
    """Verify exact Mac TLS leaf certificate before sending the auth token."""
    raw=config.get('url','')
    parsed=urlsplit(raw)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/api/recorder/sessions'):
        raise FeedError('A private HTTPS session feed URL is required.')
    try:
        host=parsed.hostname or ''
        address=ipaddress.ip_address(host)
        if not (address.is_private or address.is_loopback) or address.is_multicast or address.is_unspecified:
            raise ValueError()
        port=parsed.port or 443
    except (ValueError,TypeError):
        raise FeedError('Use a numeric private LAN IP for the Mac session feed.') from None
    fingerprint=str(config.get('fingerprint','')).lower().replace(':','').strip()
    if not _FP.fullmatch(fingerprint):
        raise FeedError('Mac TLS certificate fingerprint is required for pairing.')
    token=config.get('token')
    if not isinstance(token,str) or len(token)<20 or len(token)>256 or '\n' in token or '\r' in token:
        raise FeedError('A valid session-feed pairing token is required.')
    # CERT_NONE is intentional here: exact SHA-256 leaf pin is checked BEFORE any HTTP
    # authorization header is sent. No TOFU, redirects, or public hosts are allowed.
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname=False
    context.verify_mode=ssl.CERT_NONE
    con=http.client.HTTPSConnection(host,port,context=context,timeout=timeout)
    try:
        con.connect()
        digest=hashlib.sha256(con.sock.getpeercert(binary_form=True)).hexdigest()
        if not hmac.compare_digest(digest,fingerprint):
            raise FeedError('Mac TLS certificate fingerprint did not match. No credentials sent.')
        con.request('GET','/api/recorder/sessions',headers={
            'Authorization':'Bearer '+token,'Accept':'application/json','Cache-Control':'no-store'})
        response=con.getresponse()
        if response.status!=200:
            raise FeedError('Session feed authorization or service unavailable (HTTP %s).' % response.status)
        if int(response.getheader('Content-Length','0'))>131072:
            raise FeedError('Session feed response is too large.')
        data=response.read(131073)
        if len(data)>131072:
            raise FeedError('Session feed response is too large.')
        return validate_public_sessions(json.loads(data))
    except (OSError,ssl.SSLError,http.client.HTTPException,ValueError,json.JSONDecodeError) as exc:
        raise FeedError('Cannot reach or validate the paired Mac session feed.') from exc
    finally:
        con.close()


class SessionFeed:
    """Controller-local cache; refuses to present stale snapshots as 'connected'."""
    def __init__(self,filename:Path, refresh_seconds:int=8):
        self.filename=Path(filename)
        self.refresh_seconds=refresh_seconds
        self.lock=threading.Lock()
        self.last_attempt=0.0
        self.last_result={'state':'not_configured','sessions':[],'message':'Pair with the Mac Admin session feed to show assigned classes.'}

    def snapshot(self):
        with self.lock:
            now=time.monotonic()
            if now-self.last_attempt<self.refresh_seconds:
                return dict(self.last_result)
            self.last_attempt=now
            if not self.filename.is_file():
                self.last_result={'state':'not_configured','sessions':[],'message':'No Mac session feed has been paired.'}
                return dict(self.last_result)
            try:
                if self.filename.is_symlink():
                    raise FeedError('Refusing symlink configuration.')
                config=json.loads(self.filename.read_text(encoding='utf8'))
                items=fetch_pinned_sessions(config)
                self.last_result={'state':'connected','sessions':items,'syncedAtEpoch':int(time.time()),
                                  'message':'Assigned by the DocTutorials Mac Admin portal. Scheduling does not prove Zoom is live.'}
            except (OSError,ValueError,FeedError,json.JSONDecodeError):
                self.last_result={'state':'disconnected','sessions':[],
                                  'message':'Mac Admin feed unavailable or pairing invalid. No old assignments shown as current.'}
            return dict(self.last_result)
