"""Read the EXISTING DocTutorials Admin/Faculty session registry without duplicating classes.

This is a read-only adapter for the original DocTutorials Live demo's SQLite
`SessionStore` database. Meeting IDs, passcodes and participant data are NEVER
returned to the dashboard. A database must be placed on the Windows host first;
there is no Mac bridge and no fabricated session data.
"""
from __future__ import annotations

import os
from contextlib import closing
from pathlib import Path
import sqlite3

DEFAULT_ADMIN_DB = Path.home() / '.config' / 'doctutorials' / 'demo-live-sessions.sqlite3'
PUBLIC_FIELDS = ('sessionId', 'facultyId', 'course', 'subject', 'topic', 'startsAt', 'endsAt')


class ExistingAdminSessions:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or os.environ.get('DOCTUTORIALS_ADMIN_DB', '') or DEFAULT_ADMIN_DB).expanduser()

    def snapshot(self):
        if not self.path.is_file() or self.path.is_symlink():
            return {'state': 'admin_data_missing', 'sessions': [],
                    'message': 'Existing Admin assignments are not on this Windows PC yet. Do not enter classes again; migrate the Admin database once.'}
        try:
            uri = self.path.resolve().as_uri() + '?mode=ro'
            with closing(sqlite3.connect(uri, uri=True, timeout=4)) as db:
                rows = db.execute('''SELECT session_id, faculty_id, course, subject,
                    topic, starts_at, ends_at FROM sessions
                    ORDER BY starts_at, session_id LIMIT 1000''').fetchall()
            result=[]
            for row in rows:
                session_id, faculty_id, course, subject, topic, starts_at, ends_at = row
                if not all(isinstance(v,str) and v for v in (session_id,faculty_id,course,subject,topic)):
                    continue
                if not isinstance(starts_at,int) or not isinstance(ends_at,int) or starts_at>=ends_at:
                    continue
                # Faculty name is absent from the original database. Do not invent one.
                result.append({'sessionId':session_id, 'facultyId':faculty_id,
                    'course':course, 'subject':subject, 'topic':topic,
                    'startsAt':starts_at, 'endsAt':ends_at})
            return {'state':'existing_admin', 'sessions':result,
                    'message':'Read-only assignments from the original DocTutorials Admin database. This is schedule information, not observed Zoom live status.'}
        except (sqlite3.Error, OSError):
            # Never expose SQL errors, DB values, or credentials through the API.
            return {'state':'admin_data_unavailable', 'sessions':[],
                    'message':'The existing Admin database cannot be read. Check its format, location and Windows permissions.'}
