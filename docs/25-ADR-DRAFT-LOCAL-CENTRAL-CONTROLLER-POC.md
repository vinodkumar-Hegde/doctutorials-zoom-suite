# ADR draft — Standalone local Windows recorder proof of concept (2026-11-15)

**Status:** PROPOSED, not reviewed for production.

**Operator scope:** DocTutorials Central Controller with four independent recording channels, screen plus faculty video layout, local MP4 storage and verified office NAS copy. This overrides the earlier temporary Windows-work pause only for prototype development.

**Implementation:** A separate loopback-only Python controller supervises isolated FFmpeg media-composition processes. A channel receives separately configured teaching video, faculty video and audio inputs. Files are segmented locally, finalized to MP4, catalogued, and optionally copied to NAS with SHA-256 checks. Demo sources are synthetic and are visibly labeled test media.

**Hard dependencies still unverified:** Acquiring independent Zoom Meeting SDK raw share/video/audio frames, permissions and meeting-joining orchestration on Windows; four genuinely isolated Zoom media sources; reliable 8-hour sessions on office hardware; automatic integration with Admin/Faculty schedule; consent and operator security review. The sample Windows gdigrab/window+WASAPI configuration is a UI capture experiment, not SDK source isolation and not production proof.

**Safety:** No Zoom Cloud Recording or Zoom local-recording API controls are assumed. Control API remains bound to 127.0.0.1. No student recordings, Zoom IDs, passwords or secrets are committed. Do not publish this service on the LAN. Keep the working Mac/iPad stack untouched.

**Next acceptance:** Run Windows demo and unit tests, then record **one authorized real Zoom meeting** with measured audio/video. Only after one fully verified media source should the SDK adapter and multi-channel end-to-end tests proceed.
