"""Tiny Windows-friendly client for the local Meetings sandbox service.

Run in a second PowerShell terminal while meetings_api.py is listening.
Reads session key in hidden prompt and prints only counts/check results.
"""
from __future__ import annotations

import getpass
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def local_get(path: str, key: str) -> dict:
    req = Request("http://127.0.0.1:8765" + path, headers={"X-DocTutorials-Key": key})
    try:
        with urlopen(req, timeout=15) as response:
            data = response.read(1_000_001)
    except HTTPError as e:
        raise RuntimeError(f"Local API HTTP {e.code}") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Local API not reachable on 127.0.0.1:8765") from None
    if len(data) > 1_000_000:
        raise RuntimeError("Unexpected large response")
    return json.loads(data.decode("utf-8"))


def main() -> int:
    try:
        key = getpass.getpass("Paste session-only local API key (hidden): ")
        if not key:
            raise RuntimeError("Local API key is required")
        result = local_get("/v1/meetings", key)
        count = result.get("count")
        if not isinstance(count, int) or count < 0:
            raise RuntimeError("Invalid local meetings response")
        print(f"Local authenticated meetings GET: PASS, count={count}")
        if count:
            detail = local_get("/v1/meetings/1", key)
            if not isinstance(detail.get("meeting"), dict):
                raise RuntimeError("Invalid local meeting-detail response")
            print("Local authenticated first meeting detail GET: PASS")
        else:
            print("Local meeting detail GET: SKIPPED (no scheduled meetings)")
        print("RESULT: PASS — Local Zoom Basic Meetings service. No webinar APIs.")
        return 0
    except (RuntimeError, ValueError, json.JSONDecodeError, KeyboardInterrupt) as exc:
        msg = str(exc) if not isinstance(exc, KeyboardInterrupt) else "Interrupted"
        print(f"RESULT: NOT PASSED — {msg}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
