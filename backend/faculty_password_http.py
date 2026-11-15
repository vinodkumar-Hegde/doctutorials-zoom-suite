"""Default-OFF first-party sandbox faculty password login + existing iPad join route.

The Mac operator sets a static password locally; only its salted hash is
stored outside the Git repository. HTTPS login issues an opaque 15-minute
session token, verified server-side on the existing join-ticket route.

This application factory intentionally does NOT start a web listener or
configure a Zoom app secret, meeting assignment database or TLS deployment.
Do not turn it on publicly before the documented HTTPS and ingress gates.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response

from backend.faculty_password_auth import StaticFacultyPasswordAuthenticator
from backend.ipad_join_authorization import SandboxIPadJoinService
from backend.ipad_join_http import create_ipad_join_app

_MAX_LOGIN_BYTES = 4096


async def _read_json_without_unbounded_body(request: Request) -> dict[str, Any]:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(status_code=415, detail="Expected JSON.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > _MAX_LOGIN_BYTES:
            raise HTTPException(status_code=413, detail="Request too large.")
        content.extend(chunk)
    try:
        payload = json.loads(content)
    except (UnicodeError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid request.") from None
    if not isinstance(payload, dict) or set(payload) != {"facultyId", "password"}:
        raise HTTPException(status_code=400, detail="Invalid request.")
    if not isinstance(payload["facultyId"], str) or not isinstance(payload["password"], str):
        raise HTTPException(status_code=400, detail="Invalid request.")
    return payload


def create_first_party_faculty_app(
    authenticator: StaticFacultyPasswordAuthenticator,
    join_service: SandboxIPadJoinService,
    *,
    enable_password_login_api: bool = False,
    enable_ipad_join_api: bool = False,
    allowed_hosts: tuple[str, ...] = (),
):
    """Create explicit opt-in HTTPS faculty login and join endpoints.

    The sole user account is configured by trusted operator, not via an
    internet registration endpoint. Any public deployment must supply TLS
    certs, a verified proxy configuration and strict ingress IP rate limits.
    """
    if not isinstance(authenticator, StaticFacultyPasswordAuthenticator):
        raise TypeError("A configured private faculty password verifier is required.")
    if type(enable_password_login_api) is not bool:
        raise TypeError("Login API enablement must be an explicit boolean.")

    app = create_ipad_join_app(
        join_service,
        authenticator.verify_faculty_token,
        enable_ipad_join_api=enable_ipad_join_api,
        allowed_hosts=allowed_hosts,
    )

    @app.post("/api/faculty/login")
    async def faculty_login(request: Request):
        if not enable_password_login_api:
            raise HTTPException(status_code=503, detail="Faculty login is not enabled.")
        # Scope scheme is trustworthy ONLY behind correctly configured TLS
        # termination/proxy or a native HTTPS ASGI listener.
        if request.scope.get("scheme") != "https":
            raise HTTPException(status_code=426, detail="HTTPS is required.")
        payload = await _read_json_without_unbounded_body(request)
        result = authenticator.authenticate(payload["facultyId"], payload["password"])
        if result is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid faculty credentials.",
            )
        token, expires = result
        return JSONResponse({
            "accessToken": token,
            "tokenType": "Bearer",
            "expiresAtEpoch": expires,
        })

    @app.post("/api/faculty/logout", status_code=204)
    async def faculty_logout(request: Request):
        if not enable_password_login_api:
            raise HTTPException(status_code=503, detail="Faculty login is not enabled.")
        if request.scope.get("scheme") != "https":
            raise HTTPException(status_code=426, detail="HTTPS is required.")
        if await request.body():
            raise HTTPException(status_code=400, detail="Request body is not permitted.")
        header = request.headers.get("authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required.")
        token = header[len("Bearer "):]
        if authenticator.verify_faculty_token(token) is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        authenticator.revoke_token(token)
        return Response(status_code=204)

    return app
