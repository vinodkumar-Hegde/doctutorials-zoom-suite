"""Check Windows readiness without any account mutation or credential printing.

Default performs no network calls. --check-auth tests Zoom OAuth token issuance
only; neither outcome establishes RTMS subscription or credit entitlement.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
from existing_admin_sessions import ExistingAdminSessions
from zoom_rtms_ingest import ZoomRtmsReceiver, RtmsUnavailable, trusted_wss


def readiness() -> dict:
    env=os.environ
    return {
        'FFmpeg': bool(shutil.which('ffmpeg')),
        'FFprobe': bool(shutil.which('ffprobe')),
        'Existing Admin schedule': ExistingAdminSessions().snapshot()['state']=='existing_admin',
        'Configured storage file': (Path(__file__).parent/'config.json').is_file(),
        'Python websocket-client': has_websocket(),
        'RTMS app Client ID': bool(env.get('ZOOM_RTMS_CLIENT_ID')),
        'RTMS app Client Secret': bool(env.get('ZOOM_RTMS_CLIENT_SECRET')),
        'Zoom Event WebSocket URL': valid_url(env.get('ZOOM_RTMS_EVENT_WSS','')),
    }


def has_websocket():
    try:
        import websocket
        return hasattr(websocket,'WebSocketApp')
    except ImportError:
        return False


def valid_url(text):
    try:
        trusted_wss(text)
        return True
    except RtmsUnavailable:
        return False


def main(argv=None):
    ap=argparse.ArgumentParser(description='Read-only DocTutorials Zoom RTMS setup check')
    ap.add_argument('--check-auth',action='store_true',help='Test OAuth token issue only; no meeting connection')
    args=ap.parse_args(argv)
    results=readiness()
    for name,passed in results.items():
        print(f'{name}: {"PASS" if passed else "NOT READY"}')
    if args.check_auth:
        if not all(results[k] for k in ('RTMS app Client ID','RTMS app Client Secret','Zoom Event WebSocket URL')):
            print('Zoom OAuth: NOT TESTED — RTMS app settings missing')
        else:
            # Do not create a receiver or connection: call token issuance only.
            receiver=ZoomRtmsReceiver(None,lambda:{},
                client_id=os.environ['ZOOM_RTMS_CLIENT_ID'],
                client_secret=os.environ['ZOOM_RTMS_CLIENT_SECRET'],
                event_base=os.environ['ZOOM_RTMS_EVENT_WSS'])
            try:
                receiver.oauth_token()
                print('Zoom OAuth: PASS (not proof of RTMS credits or authorization)')
            except Exception:
                print('Zoom OAuth: NOT READY (check RTMS app authorization/network)')
    print('Real Zoom recording: NOT VERIFIED until an authorized RTMS meeting delivers media')
    return 0


if __name__=='__main__':raise SystemExit(main())
