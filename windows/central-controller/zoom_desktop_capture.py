"""Operator-assisted Zoom Workplace window capture for ONE Windows meeting.

No RTMS, Zoom Meeting SDK, browser screen capture or Zoom Cloud Recording.
Meeting join details stay in a Windows-local private SQLite DB and never pass
through the controller's HTTP API. The browser is a CONTROL PANEL only.

This first stage DOES NOT know when the faculty presses Start on a different
computer; a Windows-side faculty-start signal is still required. Desktop UI
layout/audio and PIP must be validated during a consented meeting.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
import ctypes
import os
import re
import subprocess
import sqlite3
import sys
import threading

from engine import RecorderError

PRIVATE_DB = Path.home() / '.config' / 'doctutorials' / 'private-live-sessions.sqlite3'
MEETING = re.compile(r'^[0-9]{9,13}$')
SESSION = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
ZOOM_EXES = {'zoom.exe', 'zoomworkplace.exe', 'cpthost.exe'}


class ZoomDesktopUnavailable(RecorderError):
    pass


@dataclass(frozen=True)
class ZoomWindow:
    hwnd: int
    width: int
    height: int


def private_meeting_for(db_path: Path, assignment: dict) -> dict:
    """Match one PRIVATE Admin DB row against the PUBLIC imported assignment.

    Never copy credential fields to responses, logs, session metadata or an
    environment variable. Mac -> Windows transfer is a one-time private file
    operation, NOT a running connection to Mac.
    """
    path = Path(db_path).expanduser()
    if not path.is_file() or path.is_symlink():
        raise ZoomDesktopUnavailable('Private Zoom meeting registry is missing on Windows. The earlier schedule-only export does not include join details.')
    session_id = assignment.get('sessionId')
    if not isinstance(session_id,str) or not SESSION.fullmatch(session_id):
        raise ZoomDesktopUnavailable('Invalid assigned session.')
    try:
        uri = path.resolve().as_uri() + '?mode=ro'
        with sqlite3.connect(uri, uri=True, timeout=4) as db:
            row = db.execute('''SELECT faculty_id, course, subject, topic, meeting_id, meeting_passcode
                                FROM sessions WHERE session_id=?''', (session_id,)).fetchone()
    except (OSError,sqlite3.Error) as exc:
        raise ZoomDesktopUnavailable('Windows private Zoom registry cannot be read.') from exc
    if not row:
        raise ZoomDesktopUnavailable('No Zoom join details for this existing Admin assignment.')
    faculty, course, subject, topic, meeting_id, passcode = row
    # Admin may reschedule a class after the private Zoom registry was exported.
    # Its unique session/faculty/course/subject/topic, not mutable times, bind its Zoom ID.
    if (faculty != assignment.get('facultyId') or course != assignment.get('course')
            or subject != assignment.get('subject') or topic != assignment.get('topic')):
        raise ZoomDesktopUnavailable('The private Zoom registry does not match the current Admin schedule; do not join a potentially wrong class.')
    if not isinstance(meeting_id,str) or not MEETING.fullmatch(meeting_id):
        raise ZoomDesktopUnavailable('Private Zoom meeting number is invalid.')
    if not isinstance(passcode,str) or len(passcode)>64 or any(ord(c)<32 for c in passcode):
        raise ZoomDesktopUnavailable('Private Zoom passcode is invalid.')
    return {'meeting_id': meeting_id, 'passcode': passcode}


def zoom_window_candidates() -> list[ZoomWindow]:
    """Only visible, nonminimized Zoom-process windows of sufficient dimensions.

    ctypes is standard library; no additional Windows window-inspection library.
    No title, participant identity or meeting number leaves this function.
    """
    if sys.platform != 'win32':
        return []
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    process_query_limited_info = 0x1000
    candidates = []
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    @enum_proc
    def visit(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        size = user32.GetWindowTextLengthW(hwnd)
        if not (1 <= size <= 250):
            return True
        title = ctypes.create_unicode_buffer(size+1)
        user32.GetWindowTextW(hwnd, title, size+1)
        name = title.value.lower()
        # The Zoom Workplace home window is NOT a meeting. Only capture the
        # dedicated Zoom Meeting window to avoid recording the app launcher.
        if 'zoom meeting' not in name:
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(process_query_limited_info,False,pid.value)
        if not handle:
            return True
        try:
            exe = ctypes.create_unicode_buffer(1024)
            n = wintypes.DWORD(1024)
            if not kernel32.QueryFullProcessImageNameW(handle,0,exe,ctypes.byref(n)):
                return True
            if Path(exe.value).name.lower() not in ZOOM_EXES:
                return True
        finally:
            kernel32.CloseHandle(handle)
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd,ctypes.byref(rect)):
            return True
        w,h = rect.right-rect.left, rect.bottom-rect.top
        if w>=640 and h>=400:
            candidates.append(ZoomWindow(int(hwnd),w,h))
        return True

    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.EnumWindows(visit,0)
    return candidates


def single_zoom_window(windows: list[ZoomWindow]) -> ZoomWindow:
    if not windows:
        raise ZoomDesktopUnavailable('No visible Zoom meeting window found on Windows. Join and open the class before recording.')
    if len(windows)!=1:
        raise ZoomDesktopUnavailable('Multiple Zoom windows detected. One-meeting desktop capture cannot safely select which class to record.')
    return windows[0]


def capture_sources(window: ZoomWindow) -> dict:
    """Window handle, not desktop-wide capture. Camera crop is only a LAYOUT ESTIMATE.

    A real Zoom meeting must show teaching share and faculty tile together.
    Faculty identity cannot be guaranteed by pixel cropping; operator must inspect.
    """
    if window.hwnd<=0 or window.width<640 or window.height<400:
        raise ZoomDesktopUnavailable('Zoom meeting window is too small or invalid.')
    w,h=window.width,window.height
    tile_w=(max(160,min(w//3,round(w*.24)))//2)*2
    tile_h=(min(h//3,round(tile_w*9/16))//2)*2
    x=max(0,w-tile_w-16)
    y=16
    if x+tile_w>w or y+tile_h>h:
        raise ZoomDesktopUnavailable('Zoom window too small for the speaker video crop.')
    return {
        'configured':True,
        'mode':'ZOOM DESKTOP WINDOW — operator-verified UI capture (NOT RTMS)',
        'screen':{'kind':'gdigrab','window_hwnd':window.hwnd},
        'faculty':{'kind':'gdigrab','window_hwnd':window.hwnd,'crop':[x,y,tile_w,tile_h]},
        'audio':{'kind':'wasapi_loopback'},
    }


class ZoomDesktopController:
    def __init__(self,private_db:Path=PRIVATE_DB,*,finder=zoom_window_candidates,launcher=None):
        self.private_db=Path(private_db)
        self.finder=finder
        self.launcher=launcher if launcher is not None else self._launch
        self.lock=threading.RLock()
        self.opened_session=None

    @staticmethod
    def _launch(url:str):
        if sys.platform!='win32':
            raise ZoomDesktopUnavailable('Zoom desktop launch is supported only on Windows.')
        # Zoom's historical desktop URL protocol may require user interaction.
        # Never log or return this credential-bearing URI.
        os.startfile(url)

    def status(self):
        windows=self.finder()
        return {'enabled':True,
                'privateMeetingData':'available' if self.private_db.is_file() else 'missing',
                'windowState':'single' if len(windows)==1 else ('missing' if not windows else 'ambiguous'),
                'captureReady':len(windows)==1,
                'openedSessionId':self.opened_session}

    def open(self,assignment:dict):
        meeting=private_meeting_for(self.private_db,assignment)
        # Unofficial zoommtg protocol; the Windows operator may have to approve
        # the OS scheme/open dialog and admit the recorder from the waiting room.
        url='zoommtg://zoom.us/join?'+urlencode({'confno':meeting['meeting_id'],'pwd':meeting['passcode']})
        with self.lock:
            self.launcher(url)
            self.opened_session=assignment['sessionId']
        return {'state':'launch_requested','message':'Zoom desktop launch requested on this Windows PC. Confirm the correct meeting, shared screen, audio and speaker tile.'}

    def preview(self,engine,assignment:dict) -> bytes:
        """Authorized single-frame Zoom-window snapshot, never desktop-wide.

        Allows a human to verify the teaching share and camera tile placement
        before recording. This is NOT a measurement of live Zoom membership.
        """
        private_meeting_for(self.private_db,assignment)
        with self.lock:
            if self.opened_session!=assignment['sessionId']:
                raise ZoomDesktopUnavailable('Open this assigned Zoom meeting first.')
            window=single_zoom_window(self.finder())
        if sys.platform!='win32':
            raise ZoomDesktopUnavailable('Zoom window preview is supported only on Windows.')
        command=[engine.ffmpeg,'-hide_banner','-loglevel','error',
                 '-f','gdigrab','-framerate','1','-draw_mouse','0',
                 '-i',f'hwnd=0x{window.hwnd:x}',
                 '-frames:v','1','-vf','scale=1280:720:force_original_aspect_ratio=decrease',
                 '-f','image2pipe','-vcodec','png','pipe:1']
        try:
            out=subprocess.run(command,capture_output=True,timeout=12,check=False)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise ZoomDesktopUnavailable('Unable to preview the Zoom meeting window.') from exc
        if out.returncode or not out.stdout.startswith(b'\x89PNG\r\n\x1a\n') or len(out.stdout)>8_000_000:
            raise ZoomDesktopUnavailable('Zoom window preview failed. Keep Zoom visible and check hardware acceleration/window capture.')
        return out.stdout

    def start_capture(self,engine,assignment:dict,consent:bool):
        if consent is not True:
            raise ZoomDesktopUnavailable('Confirm recording permission and participant notice before capturing Zoom.')
        # Recheck sensitive local mapping instead of trusting browser-supplied fields.
        private_meeting_for(self.private_db,assignment)
        channel=assignment['plannedChannel']
        with self.lock:
            if self.opened_session!=assignment['sessionId']:
                raise ZoomDesktopUnavailable('Open this assigned Zoom meeting from Windows Recording Center before starting capture.')
            if any(p.poll() is None for p in engine.processes.values()):
                raise ZoomDesktopUnavailable('Another desktop recorder is active. Audio/Zoom visual isolation is not yet verified for multiple meetings.')
            window=single_zoom_window(self.finder())
            previous=engine.channels[channel]
            engine.channels[channel]=capture_sources(window)
            meta={name:assignment[name] for name in ('sessionId','facultyId','course','subject','topic')}
            meta['faculty']=assignment['facultyId']
            try:
                return engine.start(channel,meta)
            except Exception:
                engine.channels[channel]=previous
                raise
