"""Offline tests: Stage 3 probes must not pretend to control Zoom recording."""
import struct
import tempfile
import unittest
from pathlib import Path

from backend.windows_recorder_probe import (
    RecorderProbeError, inspect_environment, inspect_sdk_dir, verify_final_mp4,
)


def box(kind: bytes, payload: bytes = b"") -> bytes:
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def sample_mp4() -> bytes:
    return (
        box(b"ftyp", b"isom\x00\x00\x02\x00isom") +
        box(b"free", b"padding") +
        box(b"mdat", b"\x00" * 128) +
        box(b"moov", b"\x00" * 32)
    )


class WindowsRecorderProbeTests(unittest.TestCase):
    def test_environment_does_not_claim_sdk_connected(self):
        info = inspect_environment(
            system="Windows",
            environ={"APPDATA": "C:/Profiles/user/AppData/Roaming"},
            exists=lambda path: str(path).replace("\\", "/").endswith("Zoom/bin/Zoom.exe"),
        )
        self.assertTrue(info["windows"])
        self.assertTrue(info["zoom_executable_candidate"])
        self.assertFalse(info["sdk_connected"])
        self.assertFalse(info["native_recording_controls_verified"])

    def test_non_windows_is_not_mistaken_for_worker(self):
        result = inspect_environment(system="Darwin", environ={"APPDATA": "/tmp"}, exists=lambda _: True)
        self.assertFalse(result["windows"])
        self.assertFalse(result["zoom_executable_candidate"])

    def test_sdk_folder_layout_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("bin", "lib", "export_h"):
                (root / name).mkdir()
            self.assertTrue(all(inspect_sdk_dir(root).values()))
            (root / "lib").rmdir()
            self.assertFalse(inspect_sdk_dir(root)["lib"])

    def test_finalized_mp4_boxes_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(sample_mp4())
            self.assertEqual(
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None),
                len(sample_mp4())
            )

    def test_wrong_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.txt"
            file.write_bytes(sample_mp4())
            with self.assertRaises(RecorderProbeError):
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None)

    def test_small_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(sample_mp4())
            with self.assertRaises(RecorderProbeError):
                verify_final_mp4(file, minimum_size=4096, interval_seconds=0, sleep=lambda _: None)

    def test_mp4_still_changing_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(sample_mp4())
            def modify(_seconds):
                with file.open("ab") as handle:
                    handle.write(b"more data")
            with self.assertRaisesRegex(RecorderProbeError, "still changing"):
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=modify)

    def test_missing_moov_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(box(b"ftyp", b"isom") + box(b"mdat", b"video" * 20))
            with self.assertRaisesRegex(RecorderProbeError, "required media"):
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None)

    def test_invalid_box_boundary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(box(b"ftyp", b"isom") + b"\xff\xff\xff\xffmdat" + b"\x00" * 100)
            with self.assertRaisesRegex(RecorderProbeError, "Invalid or incomplete"):
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None)

    def test_wrong_file_signature_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            file.write_bytes(box(b"free", b"junk" * 30) + box(b"mdat") + box(b"moov"))
            with self.assertRaisesRegex(RecorderProbeError, "Missing MP4 file-type"):
                verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None)

    def test_missing_file_rejected_without_exposing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "secret_session_meeting.mp4"
            with self.assertRaises(RecorderProbeError) as raised:
                verify_final_mp4(file)
            self.assertNotIn("secret_session", str(raised.exception))

    def test_does_not_modify_verified_mp4(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "demo.mp4"
            original = sample_mp4()
            file.write_bytes(original)
            verify_final_mp4(file, minimum_size=64, interval_seconds=0, sleep=lambda _: None)
            self.assertEqual(file.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
