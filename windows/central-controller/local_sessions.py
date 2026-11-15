"""Windows-local, operator-controlled session schedule.

This is NOT a Zoom presence detector, join service, or recording permission system.
Sessions are only scheduled metadata and are never called 'live' without an observed
Zoom media connection. Keeps scheduling in the Windows control station: no Mac.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid

class ScheduleError(ValueError):
    pass

SESSION_ID = re.compile(r'^s-[0-9a-f]{24}$')
FACULTY_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
CHANNELS = {'', '1', '2', '3', '4'}
FIELDS = ('facultyId', 'faculty', 'course', 'subject', 'topic')


def checked_text(value, field, max_length=120):
    if not isinstance(value, str):
        raise ScheduleError(f'{field} must be text.')
    clean = value.strip()
    if not clean or len(clean) > max_length or any(ord(ch) < 32 for ch in clean):
        raise ScheduleError(f'{field} is required (up to {max_length} printable characters).')
    return clean


def validate(details):
    if not isinstance(details, dict):
        raise ScheduleError('Session data must be an object.')
    values = {name: checked_text(details.get(name), name) for name in FIELDS}
    if not FACULTY_ID.fullmatch(values['facultyId']):
        raise ScheduleError('Faculty ID may contain letters, digits, - and _.')
    for name in ('startsAt', 'endsAt'):
        raw = details.get(name)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or int(raw) != raw:
            raise ScheduleError(f'{name} must be an epoch-second timestamp.')
        values[name] = int(raw)
        if values[name] < 1577836800 or values[name] > 4102444800:
            raise ScheduleError(f'{name} is outside the supported date range.')
    if not (values['startsAt'] < values['endsAt'] <= values['startsAt'] + 24*3600):
        raise ScheduleError('End time must follow start time (within 24 hours).')
    channel = str(details.get('channel', '') or '')
    if channel not in CHANNELS:
        raise ScheduleError('Channel must be empty or 1–4.')
    values['channel'] = channel
    return values


class LocalSessions:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        with closing(self._db()) as db, db:
            db.execute('''CREATE TABLE IF NOT EXISTS assigned_sessions (
                session_id TEXT PRIMARY KEY,
                faculty_id TEXT NOT NULL,
                faculty TEXT NOT NULL,
                course TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                starts_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL,
                channel TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT 'scheduled'
                    CHECK(state IN ('scheduled','cancelled')),
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_assigned_sessions_window ON assigned_sessions(starts_at,ends_at)')

    def _db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=15000')
        return db

    @staticmethod
    def _as_json(row):
        return {
            'sessionId': row['session_id'], 'facultyId': row['faculty_id'],
            'faculty': row['faculty'], 'course': row['course'],
            'subject': row['subject'], 'topic': row['topic'],
            'startsAt': row['starts_at'], 'endsAt': row['ends_at'],
            'channel': row['channel'], 'state': row['state'],
        }

    @staticmethod
    def _check_channel_overlap(db, details, exclude=None):
        if not details['channel']:
            return
        hit = db.execute('''SELECT session_id FROM assigned_sessions
            WHERE state = 'scheduled' AND channel = ?
            AND starts_at < ? AND ends_at > ? AND session_id != ? LIMIT 1''',
            (details['channel'], details['endsAt'], details['startsAt'], exclude or '')).fetchone()
        if hit:
            raise ScheduleError('Another class already occupies this recording channel at that time.')

    def list(self):
        with self.lock, closing(self._db()) as db:
            rows = db.execute('''SELECT * FROM assigned_sessions
                ORDER BY CASE state WHEN 'scheduled' THEN 0 ELSE 1 END,
                    starts_at ASC, session_id ASC LIMIT 1000''').fetchall()
        return [self._as_json(row) for row in rows]

    def create(self, details):
        values = validate(details)
        session_id = 's-' + uuid.uuid4().hex[:24]
        now = int(time.time())
        with self.lock, closing(self._db()) as db, db:
            self._check_channel_overlap(db, values)
            db.execute('''INSERT INTO assigned_sessions
                (session_id,faculty_id,faculty,course,subject,topic,
                starts_at,ends_at,channel,state,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,'scheduled',?,?)''',
                (session_id,values['facultyId'],values['faculty'],values['course'],
                 values['subject'],values['topic'],values['startsAt'],values['endsAt'],
                 values['channel'],now,now))
        return {'sessionId':session_id, **values, 'state':'scheduled'}

    def cancel(self, session_id):
        if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
            raise ScheduleError('Invalid session ID.')
        with self.lock, closing(self._db()) as db, db:
            cur = db.execute('''UPDATE assigned_sessions SET state='cancelled',
                updated_at=? WHERE session_id=? AND state='scheduled' ''',
                (int(time.time()), session_id))
            if not cur.rowcount:
                raise ScheduleError('Scheduled session not found.')
        return {'sessionId': session_id, 'state':'cancelled'}

    def snapshot(self):
        return {'state':'local_windows', 'message':'Windows Admin schedule (not Zoom live status).',
                'sessions':self.list()}
