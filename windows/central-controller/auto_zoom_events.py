"""Experimental Zoom MEETING EVENT -> Windows Zoom Workplace capture automation.

No Zoom RTMS and no browser recording. The actual media source remains the Zoom
Workplace desktop window and Windows speaker loopback. Uses ordinary, account-
scoped Zoom `meeting.started` / `meeting.ended` events, NOT media events.

Does NOT bypass Zoom waiting rooms, authentication, notice or capture restrictions.
A working, isolated single meeting is a prerequisite for production use.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, urlopen

from zoom_desktop_capture import ZoomDesktopUnavailable
from engine import RecorderError

_MEETING_ID = re.compile(r'^[0-9]{9,13}$')
_ALLOWED_EVENTS = {'meeting.started', 'meeting.ended'}


class ZoomAutoUnavailable(RuntimeError):
    pass


def zoom_event_wss(value: str) -> str:
    """Restrict OAuth-bearing WebSocket URL to Zoom's HTTPS transport."""
    if not isinstance(value, str) or len(value) > 2048:
        raise ZoomAutoUnavailable('Invalid Zoom event connection URL.')
    parsed = urlsplit(value)
    host = (parsed.hostname or '').lower()
    if (parsed.scheme != 'wss' or
        not (host == 'zoom.us' or host.endswith('.zoom.us') or host == 'zoom.com' or host.endswith('.zoom.com')) or
        parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment):
        raise ZoomAutoUnavailable('Zoom event URL must be an official wss:// Zoom endpoint.')
    return value


def match_zoom_meeting(private_db: Path, plan: dict, meeting_id: str, *, now: int | None = None) -> dict:
    """Exact meeting-number -> original Admin session, not approximate schedule matching.

    Schedule timestamps are intentionally not used to equate DB revisions: the
    original session may have been rescheduled between exports. Class identity,
    faculty, course, subject, topic and the time-window are required instead.
    """
    meeting_id = str(meeting_id)
    if not _MEETING_ID.fullmatch(meeting_id):
        raise ZoomAutoUnavailable('Invalid meeting identity.')
    path = Path(private_db).expanduser()
    if not path.is_file() or path.is_symlink():
        raise ZoomAutoUnavailable('Private Zoom meeting registry unavailable.')
    try:
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=4) as db:
            rows = db.execute('''SELECT session_id,faculty_id,course,subject,topic FROM sessions
                                 WHERE meeting_id=? LIMIT 8''', (meeting_id,)).fetchall()
    except (sqlite3.Error, OSError) as exc:
        raise ZoomAutoUnavailable('Unable to read private Zoom registry.') from exc
    now = int(time.time()) if now is None else int(now)
    sessions = plan.get('sessions', [])
    valid = []
    for sid, fid, course, subject, topic in rows:
        for s in sessions:
            if (s.get('sessionId') == sid and s.get('facultyId') == fid and
                s.get('course') == course and s.get('subject') == subject and
                s.get('topic') == topic and
                s.get('plannedChannel') in ('1','2','3','4') and
                int(s.get('startsAt', 10**18)) - 900 <= now < int(s.get('endsAt', 0)) + 900):
                valid.append(dict(s))
    if len(valid) != 1:
        raise ZoomAutoUnavailable('Zoom meeting does not uniquely match one active Admin class.')
    return valid[0]


class AutoDesktopRecorder:
    """One-meeting automation. Never mixes two meetings into Windows audio.

    Host's `meeting.started` event opens Zoom, then capture starts only when a
    NEW visible Zoom Meeting window is observed. This is *not* proof of join
    acceptance or Goodnotes/faculty video correctness. Zoom may block the join.
    """
    def __init__(self, engine, desktop, plan, *, notice_approved: bool = False,
                 window_timeout: float = 90, poll_seconds: float = 1,
                 clock=None, sleep=None):
        self.engine, self.desktop, self.plan = engine, desktop, plan
        self.notice_approved = notice_approved
        self.window_timeout, self.poll_seconds = window_timeout, poll_seconds
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.lock = threading.RLock()
        self.current = None
        self.last = {'phase': 'waiting_for_zoom_event', 'problem': ''}
        self._seen = set()

    def status(self) -> dict:
        with self.lock:
            return dict(self.last, enabled=True, noticeApproved=self.notice_approved)

    def _set(self, phase: str, problem: str = '') -> None:
        with self.lock:
            self.last = {'phase': phase, 'problem': problem}

    def handle_event(self, event: str, body: dict) -> bool:
        if event not in _ALLOWED_EVENTS or not isinstance(body, dict):
            return False
        obj = body.get('payload', {}).get('object', {}) if isinstance(body.get('payload'), dict) else {}
        if not isinstance(obj, dict):
            return False
        number = str(obj.get('id', ''))
        instance = obj.get('uuid', '')
        if not _MEETING_ID.fullmatch(number) or not isinstance(instance, str) or not instance or len(instance) > 256:
            return False
        if event == 'meeting.ended':
            with self.lock:
                cur = self.current
                if not cur or cur['meeting'] != number or cur['instance'] != instance:
                    return False
                cur['stop'].set()
            with self.lock:
                watching = cur['watching']
            if not watching:
                threading.Thread(target=self._finish, args=(cur,), daemon=True).start()
            return True
        if not self.notice_approved:
            self._set('blocked', 'Recording notice/permission policy has not been approved for unattended capture.')
            return False
        try:
            assignment = match_zoom_meeting(self.desktop.private_db, self.plan(), number)
        except ZoomAutoUnavailable as exc:
            self._set('blocked', str(exc))
            return False
        with self.lock:
            identity = (number, instance)
            if identity in self._seen:
                return False
            if self.current is not None or any(p.poll() is None for p in self.engine.processes.values()):
                self._set('blocked', 'Another capture is active; isolated audio for a second class is unavailable.')
                return False
            # A pre-existing Zoom Meeting window could be a different class.
            if self.desktop.finder():
                self._set('blocked', 'A Zoom Meeting window was already open; cannot verify its class identity.')
                return False
            self._seen.add(identity)
            cur = {'meeting': number, 'instance': instance,
                   'assignment': assignment, 'stop': threading.Event(),
                   'channel': assignment['plannedChannel'], 'recording': False, 'watching': True, 'finishing': False}
            self.current = cur
        try:
            self.desktop.open(assignment)
        except (OSError, ZoomDesktopUnavailable, ValueError) as exc:
            with self.lock:
                if self.current is cur:
                    self.current = None
            self._set('blocked', 'Zoom desktop meeting could not be launched on Windows.')
            return False
        self._set('joining')
        threading.Thread(target=self._watch, args=(cur,), daemon=True).start()
        return True

    def _watch(self, cur: dict) -> None:
        try:
            deadline = self.clock() + self.window_timeout
            while self.clock() < deadline and not cur['stop'].is_set():
                windows = self.desktop.finder()
                if len(windows) == 1:
                    if cur['stop'].is_set():
                        break
                    try:
                        self.desktop.start_capture(self.engine, cur['assignment'], True)
                        with self.lock:
                            cur['recording'] = True
                        self._set('capture_started_unverified', 'Zoom meeting window observed; actual screen/video/audio still need acceptance testing.')
                    except (RecorderError, OSError, ValueError):
                        self._set('blocked', 'Zoom window appeared but capture could not start.')
                    return
                if len(windows) > 1:
                    self._set('blocked', 'Several Zoom windows detected; cannot select the correct meeting.')
                    break
                self.sleep(self.poll_seconds)
            if not cur['stop'].is_set() and self.status()['phase'] != 'blocked':
                self._set('blocked', 'Zoom meeting window not found; join prompt or waiting room may be blocking capture.')
        finally:
            with self.lock:
                cur['watching'] = False
                stopped = cur['stop'].is_set()
                if self.current is cur and not cur['recording'] and not stopped:
                    self.current = None
            if stopped:
                self._finish(cur)

    def _finish(self, cur: dict) -> None:
        with self.lock:
            if self.current is not cur:
                return
            if cur['finishing']:
                return
            cur['finishing'] = True
            recording = cur['recording']
            self._set('finalizing' if recording else 'ended_before_capture')
        if recording:
            try:
                self.engine.stop(cur['channel'])
                self._set('saved_to_storage_center')
            except Exception:
                self._set('recording_needs_recovery', 'Recording stop/verification failed; inspect Storage Center for recovery.')
        with self.lock:
            if self.current is cur:
                self.current = None

    def close(self) -> None:
        with self.lock:
            if self.current:
                self.current['stop'].set()


class ZoomMeetingEventListener:
    """Account event WebSocket (not RTMS). Outbound only; no public port."""
    def __init__(self, recorder: AutoDesktopRecorder, *, client_id: str,
                 client_secret: str, event_wss: str):
        if not all(isinstance(v, str) and v.strip() for v in
                   (client_id, client_secret)):
            raise ZoomAutoUnavailable('Zoom event WebSocket Client ID or Client Secret missing.')
        self.recorder = recorder
        self.client_id, self.secret = client_id, client_secret
        self.event_wss = zoom_event_wss(event_wss)
        self._closed = threading.Event()
        self._socket = None
        self._thread = None

    def _token(self) -> str:
        auth = base64.b64encode((self.client_id + ':' + self.secret).encode('utf8')).decode('ascii')
        # Zoom Event WebSocket grant, verified by Windows diagnostic:
        # client_credentials PASS + WebSocket CONNECTED. Standard
        # account_credentials returned HTTP 400 for this event endpoint.
        form = urlencode({'grant_type': 'client_credentials'}).encode('ascii')
        req = Request('https://zoom.us/oauth/token', data=form, method='POST',
                      headers={'Authorization': 'Basic ' + auth,
                               'Content-Type': 'application/x-www-form-urlencoded'})
        with urlopen(req, timeout=20) as response:
            data = json.loads(response.read(100_000))
        token = data.get('access_token')
        if not isinstance(token, str) or not token:
            raise ZoomAutoUnavailable('Zoom meeting-event OAuth token could not be obtained.')
        return token

    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name='doctutorials-zoom-event-listener')
        self._thread.start()

    def _run(self) -> None:
        try:
            import websocket
        except ImportError:
            self.recorder._set('blocked', 'Python websocket-client is missing.')
            return
        while not self._closed.is_set():
            try:
                token = self._token()
                parsed = urlsplit(self.event_wss)
                query = dict(parse_qsl(parsed.query, keep_blank_values=True))
                query['access_token'] = token
                url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), ''))
                def on_open(sock):
                    # Show actual transport readiness rather than inferring it
                    # solely from a running controller process. Do not replace
                    # an active recording status on WebSocket reconnect.
                    if self.recorder.status().get('phase') in (
                            'waiting_for_zoom_event', 'event_connection_unavailable',
                            'event_disconnected'):
                        self.recorder._set('event_connected_waiting_for_meeting')
                    def heartbeat():
                        while not self._closed.wait(30):
                            try:
                                if not sock.sock or not sock.sock.connected:
                                    return
                                sock.send(json.dumps({'module':'heartbeat'}))
                            except (OSError, websocket.WebSocketException):
                                return
                    sock.send(json.dumps({'module':'heartbeat'}))
                    threading.Thread(target=heartbeat, daemon=True).start()
                def on_message(sock, message):
                    try:
                        frame = json.loads(message)
                        if frame.get('module') != 'message':
                            return
                        data = frame.get('content', {})
                        body = json.loads(data) if isinstance(data, str) else data
                        if isinstance(body, dict):
                            self.recorder.handle_event(body.get('event'), body)
                    except (ValueError, TypeError):
                        return
                self._socket = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message)
                self._socket.run_forever(ping_interval=25, ping_timeout=10)
                if not self._closed.is_set() and self.recorder.status().get('phase') == 'event_connected_waiting_for_meeting':
                    self.recorder._set('event_disconnected', 'Zoom event WebSocket disconnected; reconnecting.')
            except Exception:
                # Do not log OAuth token, wss URL, meeting IDs or credentials.
                self.recorder._set('event_connection_unavailable', 'Check Zoom meeting event subscription and app authorization.')
            self._closed.wait(10)

    def close(self) -> None:
        self._closed.set()
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass