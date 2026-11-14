"""Local-only, authenticated Zoom Basic sandbox Meetings API.

Install backend/requirements-local.txt, then launch:
    python -m backend.meetings_api

This is NOT a production service. It intentionally binds to 127.0.0.1 and
disables public interactive API documentation and access logs.
"""
from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader

from backend.meetings_service import SandboxMeetingsService
from backend.zoom_s2s_smoke_test import (
    SmokeTestError,
    ZoomCredentials,
    ZoomReadOnlyClient,
    get_credential,
)

_KEY_HEADER = APIKeyHeader(name="X-DocTutorials-Key", auto_error=False)


def create_app(service: SandboxMeetingsService, local_key: str) -> FastAPI:
    if not isinstance(local_key, str) or len(local_key) < 32:
        raise ValueError("A strong 32+ character local operator key is required.")

    app = FastAPI(
        title="DocTutorials Sandbox Meetings (Local Only)",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def check_key(candidate: Annotated[str | None, Depends(_KEY_HEADER)]) -> None:
        if not candidate or not secrets.compare_digest(candidate, local_key):
            raise HTTPException(status_code=401, detail="Not authorized.")

    @app.get("/v1/meetings", dependencies=[Depends(check_key)])
    def list_meetings():
        try:
            meetings = service.list_meetings()
        except SmokeTestError:
            raise HTTPException(status_code=502, detail="Zoom Meetings read failed.") from None
        return {"count": len(meetings), "meetings": meetings}

    @app.get("/v1/meetings/{ordinal}", dependencies=[Depends(check_key)])
    def get_meeting(ordinal: int):
        try:
            meeting = service.get_meeting(ordinal)
        except SmokeTestError:
            raise HTTPException(status_code=502, detail="Zoom Meetings read failed.") from None
        if meeting is None:
            raise HTTPException(status_code=404, detail="Meeting not found.")
        return {"meeting": meeting}

    return app


def main() -> None:
    import uvicorn

    credentials = ZoomCredentials(
        account_id=get_credential("ZOOM_ACCOUNT_ID", "Zoom Basic sandbox Account ID (hidden): "),
        client_id=get_credential("ZOOM_S2S_CLIENT_ID", "Sandbox S2S Client ID (hidden): "),
        client_secret=get_credential("ZOOM_S2S_CLIENT_SECRET", "Sandbox S2S Client Secret (hidden): "),
    )
    service = SandboxMeetingsService(ZoomReadOnlyClient(credentials))
    # Confirm account type before starting the local HTTP listener.
    service.list_meetings()

    local_key = secrets.token_urlsafe(36)
    print("\nLocal API listening only on http://127.0.0.1:8765")
    print("Session-only X-DocTutorials-Key (keep private; enter when prompted by local client):")
    print(local_key)
    print("Stop the local server with Ctrl+C. Do not expose this port to a network.")
    app = create_app(service, local_key)
    uvicorn.run(app, host="127.0.0.1", port=8765, access_log=False, log_level="warning")


if __name__ == "__main__":
    main()
