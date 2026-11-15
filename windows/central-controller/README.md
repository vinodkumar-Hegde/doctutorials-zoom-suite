# DocTutorials Standalone Central Controller — four isolated recorder slots

**Real local recording core, not Zoom Cloud Recording, Zoom standard Local Recording, OBS, or browser screen capture.**

This archive contains a separately running Windows-oriented recorder that uses native OS media inputs or upstream media pipes, launches four independently monitored FFmpeg recording workers, places a configured screen + faculty video picture-in-picture + DocTutorials identity/info overlay in every frame, produces H.264/AAC MP4 video, catalogs it in a Storage Center-compatible SQLite database, and optionally archives it to office NAS using SHA-256 verification.

## What is implemented and verified

- **4 independent FFmpeg workers:** each channel has distinct session ID, capture inputs, process, segment directory, MP4, and metadata.
- **Real media composition:** teaching-screen background, separate faculty-video overlay, branding/logo and course/subject/topic/faculty strip, plus audio.
- **Long-session design:** capture H.264/AAC in 10-minute Matroska segments. On stop, FFmpeg joins/remuxes them to MP4 using stream copy **without re-encoding**. If process is interrupted, segments are preserved. `Recover` attempts remux after interruption; inspect the result before use.
- **Automatic storage:** video finalized into `<storage_root>/library/<sessionId>/<recordingId>.mp4`. The SQLite `recordings` table and file path layout match the Storage Center demo; an additional `controller_jobs` table holds channel/archival states. Play/download uses authenticated, range-enabled streaming for seeking in large files.
- **Office NAS:** copies the finished file to `<nas_root>/<sessionId>/<recordingId>.mp4.part`, verifies SHA-256, then atomically promotes to `.mp4`. If NAS fails, the verified local file remains intact and retry is available.
- **Honest state:** recording appears only after real segment bytes arrive. The demo labels all synthetic sources as **TEST MEDIA — NOT ZOOM**.
- **20 local tests passed** in this creation environment, including four concurrent real encoded videos, manual start/stop, range-playback, archive integrity/failure and credential checks. This does **not** verify Zoom SDK media subscriptions or four production Zoom meetings on the intended Windows hardware.

## Test without Zoom (Windows)

1. Extract ZIP to a folder on your Windows recording PC.
2. Install Python 3, FFmpeg (including `ffprobe`), and run `py -3 -m pip install Pillow` once. FFmpeg executables must be in PATH.
3. Double-click `start-demo-windows.bat`.
4. Choose a controller password of at least 12 characters in the terminal prompt. Do not paste it into chat.
5. Visit **http://127.0.0.1:8780** on that same Windows PC. Sign in. Start any of the four independent test channels; each generates ~6 seconds of real synthetic teaching video + camera video + audio and automatically produces an MP4 in Storage Center.
6. Press Play/Download and verify the branded mixed recording.

Alternatively, on your Mac (for an isolated recording-core test, NOT a Windows Zoom test), install Pillow and FFmpeg, then `bash start-demo-mac.sh` and use the same localhost URL. This runs independently of your existing Mac DocTutorials service on HTTPS port 8443; it does not change your iPad app, Zoom SDK, or current Admin/Faculty demo.

## Use configured real Windows capture inputs

1. Copy `config.windows-example.json` to `config.json` and set **absolute** `storage_root` (fast local SSD) and `nas_root` (a UNC share to which the recorder identity has write access). For demo local NAS copy tests, use a separate local folder instead of a NAS.
2. Configure each channel's media inputs. For a **first real Windows capture proof**, open the authorized Zoom meeting as a recording observer on the recorder Windows desktop, keep its window layout stable, configure `screen`/`faculty` as `gdigrab` window sources with measured crop rectangles, and use `audio: {"kind":"wasapi_loopback"}`. Install `py -3 -m pip install Pillow soundcard numpy` for WASAPI loopback. This produces a custom FFmpeg recording of what the **recorder machine actually sees and hears**, not Zoom's own recording. It does NOT yet guarantee a clean isolated teaching screen / webcam, because the two crops depend on the visible Zoom UI and participant layout.
3. Once you have verified *one* channel's sources, change only its `configured` to `true`, launch `start-recorder-windows.bat`, and check a short authorized test recording and audio playback.
4. Channels 2–4 must have **different independent Zoom inputs**, not cloned copies of one desktop/speaker. With regular Zoom clients, isolate each meeting in a separate Windows VM/desktop or physical workstation and provide separate media feeds to the central controller, or use separate instances of the recorder per workstation. **Four simultaneous production Zoom classes are not claimed to work on a single ordinary Zoom Workplace desktop.**

### Supported independent source kinds

| Kind | Source examples | Notes |
| --- | --- | --- |
| `gdigrab` | `{"kind":"gdigrab","window_title":"Zoom Meeting","crop":[0,0,1200,720]}` | Actual Windows window capture; crop `[x,y,width,height]` isolates an area. Windows only. |
| `dshow` | `{"kind":"dshow","device":"Your Webcam"}` or `{"kind":"dshow","device":"Stereo Mix"}` | Actual Windows camera or audio capture, depending on source position. |
| `wasapi_loopback` | `{"kind":"wasapi_loopback"}` | Actual default speaker/system playback audio of the recording Windows instance. Requires Pillow, soundcard and numpy. Distinct Zoom meetings need isolated audio endpoints. |
| `network` | `{"kind":"network","url":"srt://..."}` | Network stream delivered by a **separate configured sender/adapter**. This package does not create the sender or authenticate it. |
| `rawvideo`, `pcm` | raw `yuv420p` at specified `width`/`height`/`fps`, signed 16-bit stereo 48k PCM via configured paths/pipes | Defined input contract for a future compiled Zoom Meeting SDK raw-data adapter; the producer is **not** included. |
| `file` | `{"kind":"file","path":"D:\\Tests\\example.mp4"}` | Local test input. |
| `lavfi` | `testsrc2` / `sine` | Synthetic self-test only, clearly labeled as such. |

### Configured final video

- Resolution: **1920×1080**, 25 fps (adjustable per controller).
- Teaching screen: fills canvas with aspect ratio preserved.
- Faculty video: default ~23%-width picture-in-picture at upper-right. Customize `layout.camera_width_percent` (14–45) and `layout.camera_position` (`top-right`, `top-left`, `bottom-right`, `bottom-left`) in config.
- DocTutorials real logo at top-left, metadata strip at bottom.
- Video: H.264 (libx264); audio: AAC 48 kHz stereo.
- Segments: default 600 seconds to limit crash exposure; final MP4 is built from segments using `-c copy`.

## Outstanding integration (not included, not called working)

The Zoom Meeting SDK **raw media connector** is still required for independent, stable participant-video, shared-screen and mixed-audio sources. Zoom's Windows Meeting SDK documents `StartRawRecording`, `createRenderer`, `subscribe(userID, RAW_DATA_TYPE_SHARE / VIDEO)` and `onMixedAudioRawDataReceived` for authorized recording, with meeting host/co-host or granted local-recording permission and recording notifications. A compiled, authenticated Windows SDK adapter must acquire these frames, normalize their format/timestamps, and publish into this recorder's `rawvideo`/`pcm` or network input contract. **This package does not implement or verify those SDK operations.** The recorder also does not auto-join meetings, auto-discover scheduled sessions in your Admin dashboard, or broadcast Goodnotes from iPad; these are separate incomplete integrations. Do not consider the entire two-device solution finished.

Official Zoom docs: https://developers.zoom.us/docs/meeting-sdk/windows/default-ui/advanced-features/raw-data/
FFmpeg gdigrab docs: https://ffmpeg.org/ffmpeg-devices.html#gdigrab

## Privacy and deployment safety

- Only record authorized classes with visible participant notice and required recording permission.
- Controller binds to **127.0.0.1** and is **not** a LAN/public control API. Do not expose it with port forwarding. Use a properly authenticated TLS/VPN reverse proxy and hardened identity system before deployment beyond one controlled workstation.
- Keep `config.json` private, never place credentials or meeting links inside it. Do not copy MP4s or secrets into Git.
- Use one isolated audio device per Zoom meeting. Capturing a shared speaker on the same Windows desktop could mix participant audio from multiple classes.
- Leave headroom on local disk; NAS failures do not remove the local recording. Stress-test an actual 8-hour class and four independent physical meeting sources before production.
- Do not erase old Mac Storage Center files. This package creates/updates a catalog only in its explicitly configured `storage_root`, rather than modifying the running HTTPS demo automatically.
