"""DocTutorials standalone recorder: four isolated FFmpeg workers, no Zoom local/cloud recording.

Inputs can be real Windows GDI window capture, DirectShow device, Windows
WASAPI loopback, media files, FFmpeg test sources, or upstream raw/URL feeds.
This package does NOT itself implement the licensed Zoom Meeting SDK connector.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
VALID_STATES = {'starting','recording','stopping','finalizing','ready','failed','interrupted'}

class RecorderError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(2 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def sanitized(value, max_len=110):
    return ''.join(c for c in str(value) if c.isprintable() and c not in '\r\n')[:max_len]


def open_db(path: Path):
    db = sqlite3.connect(path, timeout=20, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=20000')
    return db


def ensure_id(value: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise RecorderError('Session ID must contain only letters, digits, - or _.')
    return value


def find_font() -> str:
    fonts = [
        r'C:\Windows\Fonts\segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/Library/Fonts/Arial.ttf',
    ]
    return next((p for p in fonts if Path(p).exists()), '')


def make_overlay(png: Path, logo: Path, meta: dict, width: int, height: int, camera: dict):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    footer = max(45, round(height * 0.075))
    draw.rectangle([0, height-footer, width, height], fill=(10, 20, 38, 235))
    pad = max(12, round(width*.015))
    font_file = find_font()
    def font(size):
        return ImageFont.truetype(font_file, size) if font_file else ImageFont.load_default()
    label = f"{sanitized(meta['course'])}  /  {sanitized(meta['subject'])}  /  {sanitized(meta['topic'])}"
    sub = f"Faculty: {sanitized(meta['faculty'])}   |   DocTutorials Live"
    draw.text((pad, height-footer+5), label[:90], font=font(max(14, footer//3)), fill='white')
    draw.text((pad, height-footer+footer//2), sub[:110], font=font(max(11, footer//4)), fill=(179, 206, 242))
    if logo.exists():
        try:
            with Image.open(logo) as opened:
                emblem = opened.convert('RGBA')
            emblem.thumbnail((round(width*.14), round(height*.085)), Image.Resampling.LANCZOS)
            # Dark backing improves legibility over teaching notes without obscuring content.
            draw.rounded_rectangle([pad-5, pad-5, pad+emblem.width+5, pad+emblem.height+5],radius=8,fill=(255,255,255,235))
            image.alpha_composite(emblem,(pad,pad))
        except (ValueError, OSError):
            pass
    x,y,w,h = camera['x'],camera['y'],camera['width'],camera['height']
    border = max(2,width//500)
    draw.rectangle([x-border,y-border,x+w+border,y+h+border],outline=(255,255,255,245),width=border)
    image.save(png)


def source_args(source: dict, *, fps: int, video: bool) -> list[str]:
    """All input source settings come from operator-owned config, not public API."""
    kind = source.get('kind')
    if kind == 'gdigrab' and video:
        if sys.platform != 'win32':
            raise RecorderError('gdigrab needs a Windows recorder workstation.')
        title = source.get('window_title')
        if not title or any(ch in title for ch in '\r\n'):
            raise RecorderError('Configure a valid Zoom window title.')
        return ['-thread_queue_size','512','-f','gdigrab','-framerate',str(fps),
                '-draw_mouse','0','-i','title='+title]
    if kind == 'dshow':
        if sys.platform != 'win32':
            raise RecorderError('DirectShow needs Windows.')
        name = source.get('device')
        if not isinstance(name,str) or not name:
            raise RecorderError('DirectShow device name is missing.')
        selector = ('video=' if video else 'audio=') + name
        args = ['-thread_queue_size','512','-f','dshow']
        if video:
            args += ['-framerate',str(fps)]
        return args + ['-i',selector]
    if kind == 'file':
        path = Path(source.get('path','')).expanduser()
        if not path.is_file():
            raise RecorderError('Configured media source file is missing.')
        return ['-stream_loop','-1','-re','-i',str(path)]
    if kind == 'network':
        url = source.get('url','')
        if not isinstance(url,str) or not url.startswith(('srt://','rtsp://','udp://','tcp://')):
            raise RecorderError('Only configured SRT/RTSP/UDP/TCP inputs are accepted.')
        return ['-thread_queue_size','512','-i',url]
    if kind == 'rawvideo' and video:
        url = source.get('path','')
        w,h = int(source.get('width',0)), int(source.get('height',0))
        if not url or min(w,h)<16 or max(w,h)>4096:
            raise RecorderError('Configure rawvideo pipe, width and height.')
        return ['-thread_queue_size','512','-f','rawvideo','-pix_fmt','yuv420p',
                '-video_size',f'{w}x{h}','-framerate',str(fps),'-i',url]
    if kind == 'pcm' and not video:
        path = source.get('path','')
        if not path:
            raise RecorderError('Configure PCM input pipe.')
        return ['-thread_queue_size','512','-f','s16le','-ar','48000','-ac','2','-i',path]
    if kind == 'lavfi':
        # Intended for functional demo/self-test, NOT a Zoom media source.
        expression = source.get('expression','')
        if not isinstance(expression,str) or len(expression)>250:
            raise RecorderError('Invalid test source expression.')
        if not expression.startswith(('testsrc','testsrc2','color=','sine=','anullsrc=')):
            raise RecorderError('Unsupported test expression.')
        return ['-f','lavfi','-i',expression]
    raise RecorderError('Unsupported or unconfigured '+('video' if video else 'audio')+' input source.')


def crop_filter(source: dict) -> str:
    crop = source.get('crop')
    if crop is None:
        return ''
    if not isinstance(crop,list) or len(crop)!=4 or not all(isinstance(v,int) and 0<=v<=8192 for v in crop):
        raise RecorderError('Crop must be [x,y,width,height] in pixels.')
    x,y,w,h = crop
    if w<16 or h<16:
        raise RecorderError('Crop must be at least 16x16 pixels.')
    return f'crop={w}:{h}:{x}:{y},'


class LoopbackAudio:
    """Windows default speaker WASAPI loopback, pushed as 48kHz stereo PCM over localhost.

    Requires soundcard and numpy. Uses the actual output device on ONE isolated
    recording workstation; don't share an audio device across Zoom channels.
    """
    def __init__(self):
        try:
            import soundcard as sc
            import numpy as np
            speaker = sc.default_speaker()
            if speaker is None:
                raise RecorderError('No Windows default speaker available for loopback.')
            mic = sc.get_microphone(id=str(speaker.id), include_loopback=True)
            if mic is None:
                raise RecorderError('Cannot access a speaker loopback microphone.')
        except ImportError as exc:
            raise RecorderError('Install soundcard and numpy to capture Windows system audio.') from exc
        self.sc,self.np,self.mic = sc,np,mic
        self.listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listener.bind(('127.0.0.1',0))
        self.listener.listen(1)
        self.listener.settimeout(1)
        self.port = self.listener.getsockname()[1]
        self.shutdown=threading.Event()
        self.error=None
        self.thread=threading.Thread(target=self._run,daemon=True)

    def start(self): self.thread.start()

    def _run(self):
        try:
            conn=None
            while not self.shutdown.is_set():
                try:
                    conn,_=self.listener.accept()
                    break
                except socket.timeout: continue
            if conn is None: return
            with conn, self.mic.recorder(samplerate=48000,channels=2) as recorder:
                while not self.shutdown.is_set():
                    frames=recorder.record(numframes=2048)
                    packed=(self.np.clip(frames,-1,1)*32767).astype('<i2').tobytes()
                    try: conn.sendall(packed)
                    except (OSError, BrokenPipeError): break
        except Exception as exc:
            self.error=type(exc).__name__ + ': ' + str(exc)[:120]
        finally:
            self.listener.close()

    def stop(self):
        self.shutdown.set()
        try: self.listener.close()
        except OSError: pass


class Engine:
    def __init__(self, config: dict):
        self.config = config
        self.root = Path(config.get('storage_root','~/.config/doctutorials/storage-center')).expanduser().resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        for part in ('staging','incoming','library'):
            (self.root/part).mkdir(exist_ok=True)
        self.logo=Path(__file__).resolve().parent/'assets'/'doctutorials-logo.png'
        self.nas = Path(config['nas_root']).expanduser() if config.get('nas_root') else None
        self.db_path = self.root/'catalog.sqlite3'
        self.lock=threading.RLock()
        self.processes={}
        self.loopbacks={}
        self.watchers={}
        self.ffmpeg=shutil.which(config.get('ffmpeg','ffmpeg'))
        self.ffprobe=shutil.which(config.get('ffprobe','ffprobe'))
        if not self.ffmpeg or not self.ffprobe:
            raise RecorderError('Install FFmpeg and FFprobe and add them to Windows PATH.')
        chans=config.get('channels',{})
        if not isinstance(chans,dict) or set(chans)!={'1','2','3','4'}:
            raise RecorderError('Configure precisely four independent channels: 1, 2, 3, 4.')
        self.channels=chans
        with self._db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS recordings (
                recording_id TEXT PRIMARY KEY,session_id TEXT NOT NULL,
                faculty_id TEXT NOT NULL,course TEXT NOT NULL,subject TEXT NOT NULL,topic TEXT NOT NULL,
                state TEXT NOT NULL,byte_size INTEGER NOT NULL DEFAULT 0,sha256 TEXT,
                created_epoch INTEGER NOT NULL,finished_epoch INTEGER,source TEXT NOT NULL DEFAULT 'recorder')''')
            db.execute('''CREATE TABLE IF NOT EXISTS controller_jobs (
                id TEXT PRIMARY KEY,channel TEXT NOT NULL,session_id TEXT NOT NULL,
                state TEXT NOT NULL,archive_state TEXT NOT NULL DEFAULT 'not_configured',
                started INTEGER NOT NULL,finished INTEGER,detail TEXT NOT NULL DEFAULT '',
                duration REAL DEFAULT 0,FOREIGN KEY(id) REFERENCES recordings(recording_id))''')
            db.execute('CREATE INDEX IF NOT EXISTS controller_jobs_channel ON controller_jobs(channel,started)')
        # A restart cannot claim an old local worker is still recording.
        with self._db() as db:
            db.execute("UPDATE controller_jobs SET state='interrupted',detail='Controller restarted; inspect staged segments' WHERE state IN ('recording','starting','stopping','finalizing')")

    def _db(self):
        class DB:
            def __enter__(inner):
                inner.db=open_db(self.db_path)
                return inner.db
            def __exit__(inner, exc_type, exc, tb):
                if exc_type: inner.db.rollback()
                else: inner.db.commit()
                inner.db.close()
        return DB()

    def _update(self,rid,**fields):
        if not fields:return
        if not set(fields)<= {'state','archive_state','detail','finished','duration'}:
            raise ValueError('Invalid job field')
        with self.lock,self._db() as db:
            db.execute('UPDATE controller_jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),rid))

    def _job(self,rid):
        with self._db() as db:
            row=db.execute('''SELECT j.*,r.faculty_id,r.course,r.subject,r.topic,
                             r.byte_size,r.sha256 FROM controller_jobs j JOIN recordings r ON r.recording_id=j.id WHERE j.id=?''',(rid,)).fetchone()
        if row is None: raise RecorderError('Unknown recording.')
        return dict(row)

    def status(self):
        items=[]
        with self._db() as db:
            for channel in ('1','2','3','4'):
                row=db.execute('''SELECT j.*,r.course,r.subject,r.topic,r.faculty_id FROM controller_jobs j
                     JOIN recordings r ON r.recording_id=j.id WHERE j.channel=? ORDER BY j.started DESC LIMIT 1''',(channel,)).fetchone()
                item={'channel':channel,'configured':self.channels[channel].get('configured',False),
                      'sourceMode':self.channels[channel].get('mode','unconfigured'),
                      'state':'idle' if row is None or row['state'] in ('ready','failed','interrupted') else row['state'],
                      'last':dict(row) if row is not None else None}
                items.append(item)
        return items

    def recordings(self):
        with self._db() as db:
            rows=db.execute('''SELECT j.*,r.faculty_id,r.course,r.subject,r.topic,r.byte_size,r.sha256
                      FROM controller_jobs j JOIN recordings r ON j.id=r.recording_id ORDER BY j.started DESC LIMIT 200''').fetchall()
        return [dict(r) for r in rows]

    def _command(self, channel: str, meta: dict, work: Path):
        config=self.channels[channel]
        screen,faculty,audio=(config.get(k,{}) for k in ('screen','faculty','audio'))
        fps=int(self.config.get('fps',25))
        width,height=int(self.config.get('width',1920)),int(self.config.get('height',1080))
        if width%2 or height%2 or not (320<=width<=3840 and 240<=height<=2160) or not (10<=fps<=60):
            raise RecorderError('Output resolution must be even, <= 3840x2160; frame rate 10–60.')
        layout=self.config.get('layout',{})
        pos=layout.get('camera_position','top-right')
        if pos not in {'top-right','top-left','bottom-right','bottom-left'}:
            raise RecorderError('Invalid faculty camera location.')
        cam_percent=int(layout.get('camera_width_percent',23))
        if not 14<=cam_percent<=45:
            raise RecorderError('Camera width must be 14–45% of canvas.')
        camw=(width*cam_percent//100)//2*2
        camh=(camw*9//16)//2*2
        footer=max(45,round(height*.075))
        margin=max(12,width//50)
        cam={'x':margin if pos.endswith('left') else width-camw-margin,
             'y':margin if pos.startswith('top') else height-footer-camh-margin,
             'width':camw,'height':camh}
        if cam['y']<0 or cam['y']+camh > height-footer:
            raise RecorderError('Camera overlay overlaps lower banner; change layout or output size.')
        overlay=work/'overlay.png'
        make_overlay(overlay,self.logo,meta,width,height,cam)
        cmd=[self.ffmpeg,'-hide_banner','-loglevel','warning','-y']
        cmd+=source_args(screen,fps=fps,video=True)
        cmd+=source_args(faculty,fps=fps,video=True)
        loopback=None
        if audio.get('kind')=='wasapi_loopback':
            if sys.platform!='win32':
                raise RecorderError('WASAPI loopback requires Windows.')
            loopback=LoopbackAudio()
            cmd+=['-thread_queue_size','512','-f','s16le','-ar','48000','-ac','2','-i',f'tcp://127.0.0.1:{loopback.port}']
        else:
            cmd+=source_args(audio,fps=fps,video=False)
        cmd+=['-loop','1','-framerate',str(fps),'-i',str(overlay)]
        # Source crops isolate teaching content and faculty tile from one or two Zoom windows.
        screen_crop=crop_filter(screen)
        faculty_crop=crop_filter(faculty)
        filters=(
           f'[0:v]{screen_crop}fps={fps},scale={width}:{height}:force_original_aspect_ratio=decrease,'
           f'pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[screen];'
           f'[1:v]{faculty_crop}fps={fps},scale={camw}:{camh}:force_original_aspect_ratio=decrease,'
           f'pad={camw}:{camh}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[faculty];'
           f'[screen][faculty]overlay={cam["x"]}:{cam["y"]}:shortest=0[composed];'
           f'[composed][3:v]overlay=0:0:format=auto,format=yuv420p[out]'
        )
        cmd+=['-filter_complex',filters,'-map','[out]','-map','2:a:0',
              '-c:v','libx264','-preset',self.config.get('preset','veryfast'),
              '-crf',str(self.config.get('crf',23)),'-pix_fmt','yuv420p',
              '-g',str(fps*2),'-c:a','aac','-ar','48000','-ac','2','-b:a','128k',
              '-max_muxing_queue_size','2048','-flush_packets','1']
        if config.get('demo_duration_seconds'):
            cmd+=['-t',str(int(config['demo_duration_seconds']))]
        cmd+=['-f','segment','-segment_time',str(int(self.config.get('segment_seconds',600))),
              '-segment_format','matroska','-reset_timestamps','1',
              str(work/'part_%05d.mkv')]
        return cmd,loopback

    def start(self,channel: str, meta: dict):
        if channel not in self.channels: raise RecorderError('Invalid channel.')
        if not self.channels[channel].get('configured'):
            raise RecorderError('Channel source not configured. No fake recording will be started.')
        for name in ('sessionId','course','subject','topic','facultyId','faculty'):
            if not isinstance(meta.get(name),str) or not meta[name].strip():
                raise RecorderError('Missing session field: '+name)
        session=ensure_id(meta['sessionId'])
        if shutil.disk_usage(self.root).free < int(self.config.get('minimum_free_bytes',1024**3)):
            raise RecorderError('Insufficient free space on the local recording disk.')
        if any(len(meta[k])>140 for k in ('course','subject','topic','facultyId','faculty')):
            raise RecorderError('Session field too long.')
        with self.lock:
            if channel in self.processes and self.processes[channel].poll() is None:
                raise RecorderError('This channel is already recording.')
            rid=uuid.uuid4().hex
            work=self.root/'staging'/rid
            work.mkdir(parents=True,exist_ok=False)
            try:
                command,loopback=self._command(channel,meta,work)
            except Exception:
                shutil.rmtree(work,ignore_errors=True)
                raise
            with self._db() as db:
                db.execute('''INSERT INTO recordings(recording_id,session_id,faculty_id,course,subject,topic,state,created_epoch,source)
                    VALUES(?,?,?,?,?,?,?,?,?)''',(
                     rid,session,meta['facultyId'],meta['course'],meta['subject'],meta['topic'],'awaiting_media',int(time.time()),'recorder'))
                db.execute('''INSERT INTO controller_jobs(id,channel,session_id,state,started) VALUES(?,?,?,?,?)''',
                          (rid,channel,session,'starting',int(time.time())))
            logfile=(work/'ffmpeg.log').open('wb')
            try:
                if loopback: loopback.start()
                flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
                proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,
                        stderr=logfile,creationflags=flags)
                self.processes[channel]=proc
                if loopback:self.loopbacks[channel]=loopback
                (work/'session.json').write_text(json.dumps({'id':rid,'channel':channel,'session':meta,
                    'started':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf8')
                watcher=threading.Thread(target=self._watch,args=(channel,rid,proc),daemon=True)
                self.watchers[rid]=watcher
                watcher.start()
            except Exception as exc:
                if loopback:loopback.stop()
                self._update(rid,state='failed',detail='Failed launching FFmpeg: '+type(exc).__name__)
                raise RecorderError('Could not launch recorder; verify FFmpeg and configured input sources.') from exc
            finally:
                logfile.close()
            return {'id':rid,'channel':channel,'state':'starting','note':'Status changes to recording only after actual media is written.'}

    def _watch(self,channel,rid,proc):
        work=self.root/'staging'/rid
        while proc.poll() is None:
            try:
                row=self._job(rid)
                if row['state']=='starting':
                    if any(p.stat().st_size>4096 for p in work.glob('part_*.mkv')):
                        self._update(rid,state='recording',detail='FFmpeg is writing actual video/audio segments')
            except (OSError,sqlite3.Error):pass
            time.sleep(.3)
        if proc.stdin and not proc.stdin.closed:
            try: proc.stdin.close()
            except OSError:pass
        if channel in self.loopbacks:self.loopbacks.pop(channel).stop()
        with self.lock:
            if self.processes.get(channel) is proc:
                self.processes.pop(channel,None)
        try:
            row=self._job(rid)
            if row['state'] in ('stopping','finalizing','ready','failed','interrupted'):
                return
            if proc.returncode==0 and list(work.glob('part_*.mkv')):
                self._finalize(rid)
            else:
                self._update(rid,state='failed',detail='FFmpeg exited before media finalized. Inspect private ffmpeg.log; partial segments preserved.')
        except Exception as exc:
            self._update(rid,state='failed',detail='Recorder finalization failed: '+str(exc)[:220])

    def stop(self,channel):
        with self.lock:
            proc=self.processes.get(channel)
            if proc is None or proc.poll() is not None:
                raise RecorderError('No running recording on this channel.')
            with self._db() as db:
                row=db.execute("SELECT id FROM controller_jobs WHERE channel=? AND state IN ('starting','recording') ORDER BY started DESC LIMIT 1",(channel,)).fetchone()
            if row is None:raise RecorderError('Running recorder has no active catalog job.')
            rid=row['id']
            self._update(rid,state='stopping',detail='Flushing live media segments')
        try:
            proc.stdin.write(b'q\n')
            proc.stdin.flush()
            proc.wait(timeout=40)
        except (OSError,subprocess.TimeoutExpired) as exc:
            self._update(rid,state='interrupted',detail='FFmpeg did not stop cleanly. Staged segments retained.')
            raise RecorderError('Recorder did not stop cleanly; inspect staged data.') from exc
        finally:
            if channel in self.loopbacks:self.loopbacks.pop(channel).stop()
        if proc.returncode!=0:
            self._update(rid,state='interrupted',detail='FFmpeg exited with error; staged media retained.')
            raise RecorderError('Recorder failed during stop; media segments preserved.')
        return self._finalize(rid)

    def _verify_mp4(self,path:Path)->float:
        result=subprocess.run([self.ffprobe,'-v','error','-show_entries','format=duration:stream=codec_name,codec_type',
                    '-of','json',str(path)],capture_output=True,text=True,timeout=60)
        if result.returncode!=0:
            raise RecorderError('FFprobe could not validate the recorded MP4.')
        try:
            obj=json.loads(result.stdout)
            codecs={(s['codec_type'],s['codec_name']) for s in obj['streams']}
            duration=float(obj['format']['duration'])
        except (ValueError,KeyError,TypeError):
            raise RecorderError('MP4 probe result incomplete.') from None
        if ('video','h264') not in codecs or ('audio','aac') not in codecs or duration<=0.2:
            raise RecorderError('Final recording must have H.264 video, AAC audio and nonzero duration.')
        return duration

    def _finalize(self,rid):
        with self.lock:
            job=self._job(rid)
            if job['state']=='ready': return job
            if job['state']=='finalizing': return job
            self._update(rid,state='finalizing',detail='Remuxing closed segments without re-encoding')
            work=self.root/'staging'/rid
            segments=sorted(work.glob('part_*.mkv'))
            if not segments:
                self._update(rid,state='interrupted',detail='No media segments present.')
                raise RecorderError('No recorded media segments found.')
            # FFmpeg concat filenames use controlled UUID staging path; escape \ and single quote.
            manifest=work/'segments.ffconcat'
            lines=['ffconcat version 1.0']
            for segment in segments:
                fn=str(segment.resolve()).replace('\\','/').replace("'", "'\\''")
                lines.append("file '"+fn+"'")
            manifest.write_text('\n'.join(lines)+'\n',encoding='utf8')
            incoming=self.root/'incoming'/(rid+'.mp4.part')
            command=[self.ffmpeg,'-hide_banner','-loglevel','error','-y',
                     '-safe','0','-f','concat','-i',str(manifest),'-map','0:v:0','-map','0:a:0',
                     '-c','copy','-movflags','+faststart','-f','mp4',str(incoming)]
            result=subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=180,text=True)
            if result.returncode!=0 or not incoming.exists():
                self._update(rid,state='interrupted',detail='MP4 remux failed; segments retained.')
                raise RecorderError('MP4 remux failed; staged media has been preserved.')
            duration=self._verify_mp4(incoming)
            digest=sha256_file(incoming)
            session=ensure_id(job['session_id'])
            target=self.root/'library'/session/(rid+'.mp4')
            target.parent.mkdir(exist_ok=True,parents=True)
            if target.exists():
                raise RecorderError('Final file already exists; refusing overwrite.')
            os.replace(incoming,target)
            finished=int(time.time())
            with self._db() as db:
                db.execute('''UPDATE recordings SET state='ready',byte_size=?,sha256=?,finished_epoch=? WHERE recording_id=?''',
                          (target.stat().st_size,digest,finished,rid))
                db.execute('''UPDATE controller_jobs SET state='ready',finished=?,duration=?,detail=?,archive_state=? WHERE id=?''',
                          (finished,duration,'MP4 verified and available in Storage Center',
                           'pending' if self.nas else 'not_configured',rid))
            if self.nas:
                threading.Thread(target=self.archive,args=(rid,),daemon=True).start()
            return self._job(rid)

    def recover(self,rid):
        with self.lock:
            job=self._job(rid)
            if job['state'] not in ('interrupted','failed'):
                raise RecorderError('Only interrupted/failed recordings may be recovered.')
            for proc in self.processes.values():
                if proc.poll() is None:
                    raise RecorderError('Stop active channels before recovering partial media.')
        return self._finalize(rid)

    def archive(self,rid):
        if self.nas is None:raise RecorderError('NAS location not configured.')
        with self.lock:
            job=self._job(rid)
            if job['state']!='ready': raise RecorderError('Only finalized videos can be archived.')
            self._update(rid,archive_state='copying')
        source=self.root/'library'/job['session_id']/(rid+'.mp4')
        target=self.nas/job['session_id']/(rid+'.mp4')
        part=target.with_suffix('.mp4.part')
        try:
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if sha256_file(target)!=job['sha256']:
                    raise RecorderError('NAS file already exists with a different checksum.')
            else:
                with source.open('rb') as fin,part.open('wb') as fout:
                    shutil.copyfileobj(fin,fout,length=4*1024*1024)
                    fout.flush()
                    os.fsync(fout.fileno())
                if sha256_file(part)!=job['sha256']:
                    raise RecorderError('NAS copy hash differs from local recording.')
                os.replace(part,target)
            self._update(rid,archive_state='verified')
        except Exception as exc:
            self._update(rid,archive_state='failed',detail='Local video ready; NAS archive failed: '+str(exc)[:130])
            # Keep partial file for operator inspection/retry, never delete local source.


    def close(self):
        """Stop and finalize all active channel processes before quitting the controller."""
        for channel in list(self.processes):
            proc=self.processes.get(channel)
            if proc is None or proc.poll() is not None:continue
            try:
                self.stop(channel)
            except RecorderError:
                if proc.poll() is None:
                    proc.kill()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:pass
        for worker in list(self.watchers.values()):
            if worker is not threading.current_thread():worker.join(timeout=35)
        for loopback in list(self.loopbacks.values()):loopback.stop()

    def media_path(self,rid):
        job=self._job(rid)
        if job['state']!='ready':raise RecorderError('This recording is not finalized.')
        path=self.root/'library'/ensure_id(job['session_id'])/(rid+'.mp4')
        if not path.is_file() or path.is_symlink():raise RecorderError('Recording file missing from local Storage Center.')
        return path
