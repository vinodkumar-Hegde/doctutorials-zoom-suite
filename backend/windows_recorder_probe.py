"""Stage 3: safe, single-channel Windows recorder readiness and MP4 artifact probe.

This is NOT a Zoom Plugin SDK adapter, recorder, or recording-control client.
It never launches meetings, invokes Zoom APIs, or modifies recordings.
Use the official Windows Plugin SDK demo to prove actual control separately.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import struct
import sys
import time
from typing import Callable


class RecorderProbeError(Exception):
    """Safe error class: callers display generic errors, never recording paths."""


def inspect_environment(
    *,
    system: str | None = None,
    environ: dict[str, str] | None = None,
    exists: Callable[[Path], bool] | None = None,
) -> dict[str, bool | str]:
    """Read-only Windows client hint check, not proof of installed client version."""
    system = platform.system() if system is None else system
    environ = os.environ if environ is None else environ
    exists = Path.is_file if exists is None else exists
    roots = [
        environ.get("APPDATA", ""),
        environ.get("LOCALAPPDATA", ""),
        environ.get("PROGRAMFILES", ""),
        environ.get("PROGRAMFILES(X86)", ""),
    ]
    candidates = [
        Path(root) / "Zoom" / "bin" / "Zoom.exe"
        for root in roots if root
    ]
    return {
        "windows": system == "Windows",
        "zoom_executable_candidate": any(exists(p) for p in candidates) if system == "Windows" else False,
        "sdk_connected": False,  # This script cannot establish an SDK IPC connection.
        "native_recording_controls_verified": False,
    }


def inspect_sdk_dir(path: Path) -> dict[str, bool]:
    """Only check required SDK directory layout, not SDK version or functionality."""
    return {
        name: (path / name).is_dir()
        for name in ("bin", "lib", "export_h")
    }


def _mp4_atoms(path: Path, file_size: int) -> set[bytes]:
    """Inspect top-level MP4 box boundaries; this does NOT validate media playback."""
    found: set[bytes] = set()
    offset = 0
    with path.open("rb") as stream:
        for _ in range(4096):
            if offset == file_size:
                return found
            if offset + 8 > file_size:
                raise RecorderProbeError("Incomplete MP4 box header.")
            stream.seek(offset)
            head = stream.read(8)
            if len(head) != 8:
                raise RecorderProbeError("Incomplete MP4 box header.")
            size32, name = struct.unpack(">I4s", head)
            header_len = 8
            if size32 == 1:
                length = stream.read(8)
                if len(length) != 8:
                    raise RecorderProbeError("Incomplete extended MP4 box header.")
                box_size = struct.unpack(">Q", length)[0]
                header_len = 16
            elif size32 == 0:
                box_size = file_size - offset
            else:
                box_size = size32
            if box_size < header_len or offset + box_size > file_size:
                raise RecorderProbeError("Invalid or incomplete MP4 box.")
            if offset == 0 and name != b"ftyp":
                raise RecorderProbeError("Missing MP4 file-type box.")
            found.add(name)
            offset += box_size
    raise RecorderProbeError("Too many MP4 boxes; verification incomplete.")


def verify_final_mp4(
    path: Path,
    *,
    minimum_size: int = 1024,
    interval_seconds: float = 2.0,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Check stable, structurally plausible MP4. Never infer successful playback.

    No writes, renames, copies or deletions. Never use while Zoom is converting.
    Returns size for non-sensitive operator summary.
    """
    if path.suffix.lower() != ".mp4" or path.is_symlink() or not path.is_file():
        raise RecorderProbeError("Provide a finalized regular MP4 file.")
    try:
        first = path.stat()
        if first.st_size < minimum_size:
            raise RecorderProbeError("MP4 is unexpectedly small.")
        sleep(interval_seconds)
        second = path.stat()
        if (first.st_size, first.st_mtime_ns) != (second.st_size, second.st_mtime_ns):
            raise RecorderProbeError("MP4 is still changing; wait for conversion.")
        atoms = _mp4_atoms(path, second.st_size)
        if not {b"ftyp", b"mdat", b"moov"}.issubset(atoms):
            raise RecorderProbeError("MP4 lacks required media or metadata boxes.")
        return second.st_size
    except OSError:
        raise RecorderProbeError("Could not safely read the finalized MP4.") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="DocTutorials one-channel Windows recorder feasibility preflight (no Zoom controls)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--environment", action="store_true", help="Report safe workstation hints.")
    group.add_argument("--sdk-dir", type=Path, help="Inspect local vendor Plugin SDK folder structure.")
    group.add_argument("--verify-mp4", type=Path, help="Check a finalized local MP4 after conversion.")
    args = parser.parse_args(argv)
    try:
        if args.environment:
            result = inspect_environment()
            print(f"Windows workstation: {'YES' if result['windows'] else 'NO'}")
            print("Zoom executable candidate: " + ("FOUND" if result["zoom_executable_candidate"] else "NOT FOUND (inspect Zoom Workplace manually)"))
            print("Plugin SDK IPC connection: NOT TESTED")
            print("Native recording command support: NOT TESTED")
            return 0 if result["windows"] else 1
        if args.sdk_dir is not None:
            found = inspect_sdk_dir(args.sdk_dir)
            for name in ("bin", "lib", "export_h"):
                print(f"Plugin SDK {name} directory: {'FOUND' if found[name] else 'NOT FOUND'}")
            print("SDK build/auth/recording behavior: NOT TESTED")
            return 0 if all(found.values()) else 1
        size = verify_final_mp4(args.verify_mp4)
        print(f"MP4 basic container and stable-file checks: PASS (bytes={size})")
        print("Video/audio playback and Zoom recording control: NOT TESTED")
        return 0
    except RecorderProbeError as exc:
        # Errors contain no user paths, meeting IDs, contents or credentials.
        print(f"RESULT: NOT PASSED — {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
