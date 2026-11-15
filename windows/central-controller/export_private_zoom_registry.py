"""Once-only offline export from original DocTutorials Admin SQLite for Windows.

Sensitive Zoom meeting IDs/passcodes. NEVER publish or upload this output.
Windows recorder must store it under the user's private .config directory.
"""
from __future__ import annotations
import os
from pathlib import Path
import sqlite3
from contextlib import closing

SOURCE=Path.home()/'.config'/'doctutorials'/'demo-live-sessions.sqlite3'
DEST=Path.home()/'Downloads'/'DocTutorialsPrivateZoomRegistry.sqlite3'

def export(source:Path=SOURCE,dest:Path=DEST):
    source,dest=Path(source),Path(dest)
    if not source.is_file() or source.is_symlink():
        raise RuntimeError('Original Admin session database not found.')
    if dest.exists():
        raise RuntimeError('Private registry export already exists. Move/delete it securely before re-exporting.')
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as old:
            rows=old.execute('''SELECT session_id,faculty_id,course,subject,topic,starts_at,ends_at,meeting_id,meeting_passcode
                                FROM sessions ORDER BY starts_at,session_id''').fetchall()
        if not rows:
            raise RuntimeError('No Admin sessions available for export.')
        handle=os.open(dest,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
        os.close(handle)
        with closing(sqlite3.connect(dest)) as out:
            with out:
                out.execute('''CREATE TABLE sessions (session_id TEXT PRIMARY KEY,faculty_id TEXT NOT NULL,
                    course TEXT NOT NULL,subject TEXT NOT NULL,topic TEXT NOT NULL,
                    starts_at INTEGER NOT NULL,ends_at INTEGER NOT NULL,
                    meeting_id TEXT NOT NULL,meeting_passcode TEXT NOT NULL)''')
                out.executemany('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?)',rows)
        if os.name=='posix':os.chmod(dest,0o600)
        return len(rows)
    except BaseException:
        if dest.is_file():dest.unlink()
        raise

if __name__=='__main__':
    n=export()
    print(f'Exported {n} original private Zoom Admin meeting assignments.')
    print(f'Securely transfer {DEST} to the Windows PC ONCE, then store under ~/.config/doctutorials/private-live-sessions.sqlite3.')
    print('WARNING: This file contains actual meeting IDs/passcodes. Never attach it to chat or GitHub; delete the transfer copy after use.')
