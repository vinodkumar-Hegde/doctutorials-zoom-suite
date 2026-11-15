"""One-time Windows pairing to Mac read-only Admin session bridge.

Stores a development-only pairing token in per-user config, never in repository.
A production deployment should store it with Windows DPAPI/credential manager.
"""
from __future__ import annotations
import getpass
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
from session_feed import fetch_pinned_sessions, FeedError


def main():
    print('DocTutorials Central: pair Windows recording PC to Mac Admin sessions')
    host=input('Mac LAN IPv4 address (e.g. 192.168.1.10): ').strip()
    try:
        addr=ipaddress.ip_address(host)
        if addr.version!=4 or not addr.is_private:raise ValueError()
    except ValueError:
        raise SystemExit('Enter a private IPv4 address for your Mac.')
    fingerprint=input('Certificate SHA256 shown by the Mac bridge: ').strip()
    if not re.fullmatch(r'[0-9a-fA-F:]{64,95}',fingerprint):
        raise SystemExit('Invalid SHA256 certificate fingerprint.')
    token=getpass.getpass('Matching session bridge secret (hidden): ')
    conf={'url':f'https://{host}:8444/api/recorder/sessions',
          'fingerprint':fingerprint.lower().replace(':',''),'token':token}
    try:
        items=fetch_pinned_sessions(conf)
    except FeedError as exc:
        raise SystemExit('Pairing failed: '+str(exc))
    root=Path(os.getenv('LOCALAPPDATA') or (Path.home()/'AppData'/'Local'))/'DocTutorials'
    root.mkdir(parents=True,exist_ok=True)
    path=root/'session-feed.json'
    flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,'w',encoding='utf8') as stream:json.dump(conf,stream)
    try:os.chmod(path,0o600)
    except OSError:pass
    print('Pairing succeeded:',len(items),'assigned sessions available. Reopen the Windows dashboard to view them.')
    print('Saved for this Windows user:',path)
    print('This prototype stores its pairing secret in a local per-user file; keep that account private.')

if __name__=='__main__':main()
