"""Read-only connection diagnostic for DocTutorials Zoom meeting EVENT WebSockets.

Does not join or record meetings. Never prints URL query, Zoom account IDs,
client secrets, OAuth access tokens, or untrusted exception text.

Zoom WebSocket docs describe client_credentials, while standard Zoom S2S
documentation describes account_credentials. Probe both independently.
"""
from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen


def _valid_zoom_wss(value: str) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        u = urlsplit(value)
        host = (u.hostname or '').lower()
        return (u.scheme == 'wss' and host in ('ws.zoom.us', 'zoom.us', 'ws.zoom.com', 'zoom.com')
                and not u.username and not u.password and u.port in (None, 443)
                and not u.fragment and u.path in ('/ws', '/ws/')
                and bool(dict(parse_qsl(u.query)).get('subscriptionId'))
                and 'access_token' not in dict(parse_qsl(u.query)))
    except ValueError:
        return False


def _request_token(client_id: str, client_secret: str, grant: str, account_id: str) -> tuple[str, str | None]:
    auth = base64.b64encode((client_id + ':' + client_secret).encode()).decode('ascii')
    form = {'grant_type': grant}
    if grant == 'account_credentials':
        if not account_id:
            return 'MISSING ACCOUNT ID', None
        form['account_id'] = account_id
    request = Request('https://zoom.us/oauth/token',
                      data=urlencode(form).encode('ascii'), method='POST',
                      headers={'Authorization': 'Basic ' + auth,
                               'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urlopen(request, timeout=15) as r:
            data = json.loads(r.read(65536))
        token = data.get('access_token')
        if isinstance(token, str) and token:
            return 'PASS', token
        return 'NO ACCESS TOKEN', None
    except HTTPError as exc:
        return 'HTTP ' + str(exc.code), None
    except (URLError, OSError, ValueError, KeyError):
        return 'NETWORK OR RESPONSE ERROR', None


def _check_websocket(wss: str, token: str) -> str:
    try:
        import websocket
    except ImportError:
        return 'MISSING websocket-client'
    u = urlsplit(wss)
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q['access_token'] = token
    full = urlunsplit((u.scheme, u.netloc, u.path, urlencode(q), ''))
    try:
        ws = websocket.create_connection(full, timeout=12, enable_multithread=True)
        try:
            ws.send(json.dumps({'module': 'heartbeat'}))
        finally:
            ws.close()
        return 'CONNECTED (handshake + heartbeat; no event triggered)'
    except Exception as exc:
        # Never print the exception: it may contain an access_token URL.
        if isinstance(exc, websocket.WebSocketBadStatusException):
            code = getattr(exc, 'status_code', None)
            if isinstance(code, int) and 100 <= code <= 599:
                return 'REJECTED HTTP ' + str(code)
        if isinstance(exc, websocket.WebSocketTimeoutException):
            return 'CONNECTION TIMEOUT'
        return 'CONNECTION FAILED (' + type(exc).__name__ + ')'


def main() -> int:
    env = os.environ
    fields = [('ZOOM_EVENTS_CLIENT_ID', 'Client ID'),
              ('ZOOM_EVENTS_CLIENT_SECRET', 'Client Secret'),
              ('ZOOM_EVENTS_ACCOUNT_ID', 'Account ID'),
              ('ZOOM_EVENTS_WSS', 'Event WebSocket URL')]
    for key, name in fields:
        print(name + ': ' + ('SET' if env.get(key) else 'MISSING'))
    if not all(env.get(k) for k, _ in fields):
        print('Diagnosis: required Zoom event settings missing in this PowerShell session.')
        return 1
    if not _valid_zoom_wss(env['ZOOM_EVENTS_WSS']):
        print('WebSocket URL: INVALID (must be wss://ws.zoom.us/ws?subscriptionId=...)')
        return 1
    print('WebSocket URL format: PASS')
    attempts = []
    for grant in ('client_credentials', 'account_credentials'):
        status, token = _request_token(env['ZOOM_EVENTS_CLIENT_ID'],
                                        env['ZOOM_EVENTS_CLIENT_SECRET'],
                                        grant, env['ZOOM_EVENTS_ACCOUNT_ID'])
        print('Zoom OAuth ' + grant + ': ' + status)
        if token:
            attempts.append((grant, token))
    if not attempts:
        print('Diagnosis: OAuth failed. Confirm DocTutorials-Backend app ACTIVATION, scopes and credentials.')
        return 2
    for grant, token in attempts:
        status = _check_websocket(env['ZOOM_EVENTS_WSS'], token)
        print('Zoom WebSocket using ' + grant + ': ' + status)
        if status.startswith('CONNECTED'):
            print('Next: restart the controller; then test with a FUTURE scheduled faculty meeting.')
            return 0
    print('Diagnosis: OAuth works but event WebSocket did not connect. Check subscription, scopes and Zoom app activation.')
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
