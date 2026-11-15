"""One-time, secret-free schedule-only export of the original DocTutorials Admin DB.

Run on the Mac that currently hosts the original Admin demo. Result contains
ONLY session metadata; no Zoom meeting ID, passcode, JWT, faculty password or
Zoom credential. Transfer the resulting file to the Windows recording PC by
an approved secure offline method; no permanent Mac/Windows bridge is needed.
"""
from __future__ import annotations
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import uuid

SOURCE = Path.home() / '.config' / 'doctutorials' / 'demo-live-sessions.sqlite3'
DEST = Path.home() / 'Downloads' / 'DocTutorialsAdminSchedule.sqlite3'
DDL = '''CREATE TABLE sessions (session_id TEXT PRIMARY KEY,
   faculty_id TEXT NOT NULL, course TEXT NOT NULL, subject TEXT NOT NULL,
   topic TEXT NOT NULL, starts_at INTEGER NOT NULL, ends_at INTEGER NOT NULL)'''
SELECT = '''SELECT session_id, faculty_id, course, subject, topic, starts_at, ends_at
    FROM sessions ORDER BY starts_at, session_id'''


def export(source: Path = SOURCE, dest: Path = DEST) -> int:
    source=Path(source).expanduser()
    dest=Path(dest).expanduser()
    if not source.is_file() or source.is_symlink():
        raise ValueError('Original Admin database not found at the expected Mac location.')
    if source.resolve()==dest.resolve():
        raise ValueError('Export path cannot overwrite the original Admin database.')
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=dest.with_name('.doctutorials-schedule-export-'+uuid.uuid4().hex+'.sqlite3')
    try:
        uri=source.resolve().as_uri()+'?mode=ro'
        with closing(sqlite3.connect(uri,uri=True,timeout=5)) as source_db:
            rows=source_db.execute(SELECT).fetchall()
        fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        os.close(fd)
        with closing(sqlite3.connect(tmp)) as output:
            with output:
                output.execute(DDL)
                output.executemany('INSERT INTO sessions VALUES (?,?,?,?,?,?,?)',rows)
        os.replace(tmp,dest)
        return len(rows)
    finally:
        tmp.unlink(missing_ok=True)

if __name__=='__main__':
    try:
        count=export()
        print(f'Exported {count} existing Admin assignments (NO Zoom credentials or passcodes): {DEST}')
        print('Move this file ONCE to the Windows PC; do not commit it to GitHub or attach it in chat.')
    except (ValueError,sqlite3.Error,OSError) as exc:
        print('Export failed: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
