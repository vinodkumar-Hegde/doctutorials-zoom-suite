#!/usr/bin/env python3
"""Read-only, credential-safe Zoom S2S OAuth smoke test for four DocTutorials hosts.

Python 3.10+; no third-party dependencies. Run only on an authorized computer.
This script does not write credentials, access tokens, user information or API data.
"""

from __future__ import annotations

import base64
import getpass
import json
import os
import sys
from dataclasses import dataclass
from typing import Callable, Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

TOKEN_URL = "https://zoom.us/oauth/token"
API_BASE = "https://api.zoom.us/v2"
PAGE_SIZE = 100
MAX_PAGES = 30
TIMEOUT_SECONDS = 20


class SmokeTestError(Exception):
    """Sanitized failure; never contains credential or Zoom response data."""


@dataclass(frozen=True)
class ZoomCredentials:
    account_id: str
    client_id: str
    client_secret: str


def get_credential(env_key: str, prompt: str) -> str:
    """Use ephemeral process env or an invisible interactive prompt (never CLI args)."""
    value = os.environ.get(env_key, "").strip()
    if not value:
        if not sys.stdin.isatty():
            raise SmokeTestError(f"{env_key} missing; use an interactive terminal.")
        value = getpass.getpass(prompt).strip()
    if not value:
        raise SmokeTestError(f"{env_key} was empty.")
    return value


def response_json(opener: Callable, req: Request, purpose: str) -> dict[str, Any]:
    try:
        with opener(req, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(5_000_001)
            if len(payload) > 5_000_000:
                raise SmokeTestError(f"{purpose}: unexpected large response.")
    except HTTPError as exc:
        # Deliberately do not print body, URL or server response headers: may contain PII.
        raise SmokeTestError(f"{purpose}: HTTP {exc.code}. Check activation, scopes, or host license.") from None
    except (URLError, TimeoutError, OSError):
        raise SmokeTestError(f"{purpose}: network/TLS error. Check secure internet access.") from None
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SmokeTestError(f"{purpose}: invalid JSON response.") from None
    if not isinstance(obj, dict):
        raise SmokeTestError(f"{purpose}: unexpected response shape.")
    return obj


class ZoomReadOnlyClient:
    def __init__(self, credentials: ZoomCredentials, opener: Callable | None = None):
        self.credentials = credentials
        self.opener = opener or urlopen
        self._access_token: str | None = None

    def authenticate(self) -> None:
        basic_bytes = f"{self.credentials.client_id}:{self.credentials.client_secret}".encode("utf-8")
        basic = base64.b64encode(basic_bytes).decode("ascii")
        body = urlencode({"grant_type": "account_credentials", "account_id": self.credentials.account_id}).encode("ascii")
        req = Request(
            TOKEN_URL,
            data=body,
            method="POST",  # OAuth token exchange only; NO Zoom resources are modified.
            headers={
                "Authorization": "Basic " + basic,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
        )
        data = response_json(self.opener, req, "OAuth token request")
        token = data.get("access_token")
        if not isinstance(token, str) or not token:
            raise SmokeTestError("OAuth token request: no usable access token returned.")
        self._access_token = token

    def get(self, path: str, params: dict[str, str | int] | None = None, *, purpose: str = "Zoom GET") -> dict:
        if self._access_token is None:
            raise SmokeTestError("Not authenticated.")
        # Refuse arbitrary URLs or paths to prevent accidentally sending token to third parties.
        if not path.startswith("/") or "//" in path or "?" in path or "#" in path:
            raise SmokeTestError("Invalid Zoom API path.")
        url = API_BASE + path
        if params:
            url += "?" + urlencode(params)
        req = Request(
            url, method="GET",
            headers={"Authorization": "Bearer " + self._access_token, "Accept": "application/json"},
        )
        return response_json(self.opener, req, purpose)

    def list_all(self, path: str, key: str, *, purpose: str, extra: dict[str, str] | None = None) -> list[dict]:
        items: list[dict] = []
        next_token = ""
        seen_tokens: set[str] = set()
        for _ in range(MAX_PAGES):
            params: dict[str, str | int] = {"page_size": PAGE_SIZE}
            if extra:
                params.update(extra)
            if next_token:
                params["next_page_token"] = next_token
            payload = self.get(path, params, purpose=purpose)
            segment = payload.get(key)
            if not isinstance(segment, list) or not all(isinstance(x, dict) for x in segment):
                raise SmokeTestError(f"{purpose}: response lacks expected {key} list.")
            items.extend(segment)
            token = payload.get("next_page_token", "") or ""
            if not isinstance(token, str):
                raise SmokeTestError(f"{purpose}: invalid pagination token.")
            if not token:
                return items
            if token in seen_tokens:
                raise SmokeTestError(f"{purpose}: repeated pagination token.")
            seen_tokens.add(token)
            next_token = token
        raise SmokeTestError(f"{purpose}: exceeded {MAX_PAGES} pages; incomplete result.")

    def list_users(self) -> list[dict]:
        return self.list_all("/users", "users", purpose="List active users", extra={"status": "active"})

    def list_meetings(self, user_id: str) -> list[dict]:
        return self.list_all(f"/users/{quote(user_id, safe='')}/meetings", "meetings", purpose="List host meetings")

    def list_webinars(self, user_id: str) -> list[dict]:
        return self.list_all(f"/users/{quote(user_id, safe='')}/webinars", "webinars", purpose="List host webinars")

    def check_meeting_detail(self, meeting_id: str | int) -> None:
        self.get(f"/meetings/{quote(str(meeting_id), safe='')}", purpose="Get meeting detail")

    def check_webinar_detail(self, webinar_id: str | int) -> None:
        self.get(f"/webinars/{quote(str(webinar_id), safe='')}", purpose="Get webinar detail")


def eligible_users(users: list[dict]) -> list[dict]:
    """Zoom user type 2 is licensed; 3 is on-prem; validate entitlements separately."""
    return [u for u in users if u.get("type") in (2, 3) and isinstance(u.get("id"), str) and u["id"]]


def choose_hosts(candidates: list[dict], input_fn: Callable[[str], str] = input) -> list[dict]:
    """Exactly four hosts; never silently choose 4 out of 5+ accounts."""
    if len(candidates) < 4:
        raise SmokeTestError(f"Only {len(candidates)} eligible active users found; expected at least 4.")
    if len(candidates) == 4:
        print("Exactly four eligible active accounts found; selecting all four.")
        return candidates
    if not sys.stdin.isatty():
        raise SmokeTestError("More than four eligible users; run interactively to select four.")
    print("LOCAL HOST PICKER (do not share a screenshot):")
    for i, user in enumerate(candidates, start=1):
        name = str(user.get("display_name") or f"Zoom user {i}")
        print(f"  {i:2d}. {name}")
    selection = input_fn("Enter exactly four host numbers separated by commas (e.g. 1,2,3,4): ").strip()
    try:
        positions = [int(x.strip()) for x in selection.split(",")]
    except ValueError:
        raise SmokeTestError("Invalid selection format; expected four numbers.") from None
    if len(positions) != 4 or len(set(positions)) != 4 or any(p < 1 or p > len(candidates) for p in positions):
        raise SmokeTestError("Select exactly four distinct valid host numbers.")
    return [candidates[p-1] for p in positions]


def run(client: ZoomReadOnlyClient) -> int:
    print("DocTutorials Zoom S2S OAuth — READ-ONLY test")
    print("No tokens, account IDs, host IDs, join links or API responses are written to disk.")
    client.authenticate()
    print("OAuth token request: PASS")
    users = client.list_users()
    print(f"List active users: PASS ({len(users)} total)")
    candidates = eligible_users(users)
    print(f"Eligible paid/on-prem host candidates: {len(candidates)}")
    hosts = choose_hosts(candidates)
    for index, user in enumerate(hosts):
        label = chr(ord("A") + index)
        user_id = user["id"]
        meetings = client.list_meetings(user_id)
        webinars = client.list_webinars(user_id)
        # The GET detail endpoint can only be tested if a non-expired scheduled item exists.
        meeting_detail = "SKIPPED (no scheduled meeting)"
        webinar_detail = "SKIPPED (no scheduled webinar)"
        if meetings:
            mid = meetings[0].get("id")
            if mid is None:
                raise SmokeTestError("Meeting list lacked a meeting ID.")
            client.check_meeting_detail(mid)
            meeting_detail = "PASS"
        if webinars:
            wid = webinars[0].get("id")
            if wid is None:
                raise SmokeTestError("Webinar list lacked a webinar ID.")
            client.check_webinar_detail(wid)
            webinar_detail = "PASS"
        print(f"Host {label}: meetings={len(meetings)}, webinars={len(webinars)}, "
              f"meeting detail={meeting_detail}, webinar detail={webinar_detail}")
    print("RESULT: PASS — four separate licensed host users were read successfully. No Zoom records modified.")
    return 0


def main() -> int:
    try:
        creds = ZoomCredentials(
            account_id=get_credential("ZOOM_ACCOUNT_ID", "Zoom Account ID (hidden): "),
            client_id=get_credential("ZOOM_S2S_CLIENT_ID", "S2S Client ID (hidden): "),
            client_secret=get_credential("ZOOM_S2S_CLIENT_SECRET", "S2S Client Secret (hidden): "),
        )
        return run(ZoomReadOnlyClient(creds))
    except (SmokeTestError, KeyboardInterrupt) as exc:
        message = "Interrupted by operator." if isinstance(exc, KeyboardInterrupt) else str(exc)
        print(f"RESULT: NOT PASSED — {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
