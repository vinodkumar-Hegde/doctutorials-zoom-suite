"""Opt-in iPad participant join-ticket HTTPS route for the Basic Zoom sandbox.

Security boundary:
* This module NEVER creates or verifies a faculty login credential.
* Only a trusted, upstream DocTutorials identity verifier may map a bearer
  token to an AuthenticatedFaculty. The verifier MUST check signature,
  issuer, audience, expiry, and revocation/active status where applicable.
* Meeting assignments are read ONLY from the server-owned repository through
  SandboxIPadJoinService; no Zoom ID, password or faculty identity is accepted
  from the iPad request body.
* An authenticating service must explicitly enable this route after HTTPS,
  allowed hosts, and faculty identity verification have been configured.
* The existing localhost-only meetings_api.py operator server is NOT reused
  or exposed to faculty.

No runnable public server, credentials, token issuer, or test login shortcut
is supplied here. Never place Zoom SDK signing secrets in a client binary.
"""
from __future__ import annotations

import re
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.ipad_join_authorization import (
    AuthenticatedFaculty,
    JoinDenied,
    SandboxIPadJoinService,
)

# A syntactically plausible opaque bearer token or JWT; cryptographic
# verification is the upstream faculty verifier's responsibility.
_BEARER = re.compile(r"^Bearer ([A-Za-z0-9._~+/-]{20,8192})$")


def create_ipad_join_app(
    join_service: SandboxIPadJoinService,
    verify_faculty_token: Callable[[str], AuthenticatedFaculty | None],
    *,
    enable_ipad_join_api: bool = False,
    allowed_hosts: tuple[str, ...] = (),
) -> FastAPI:
    """Construct a narrowly scoped HTTPS-only route, OFF by default.

    An authenticating backend supplies a verified faculty-token callback,
    server-owned assignment lookup (inside join_service), allowed hostnames,
    and explicit enablement. This is NOT a deployed or configured service.
    The actual deployment must terminate TLS correctly and set the ASGI
    scheme from a trusted reverse proxy, never from arbitrary client headers.
    """
    if not isinstance(join_service, SandboxIPadJoinService):
        raise TypeError("A trusted sandbox assignment service is required.")
    if not callable(verify_faculty_token):
        raise TypeError("A real faculty-token verifier must be supplied.")
    if type(enable_ipad_join_api) is not bool:
        raise TypeError("Enablement must be an explicit boolean.")
    if (
        not isinstance(allowed_hosts, tuple)
        or not allowed_hosts
        or any(
            not isinstance(host, str)
            or not host
            or host == "*"
            or "/" in host
            or " " in host
            for host in allowed_hosts
        )
    ):
        raise ValueError("Explicit, concrete allowed API hostnames are required.")

    app = FastAPI(
        title="DocTutorials iPad Join Tickets (Sandbox Only)",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(allowed_hosts))

    @app.middleware("http")
    async def sensitive_response_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.post("/api/sessions/{session_id}/join/ipad")
    async def issue_ipad_join_ticket(session_id: str, request: Request):
        if not enable_ipad_join_api:
            raise HTTPException(status_code=503, detail="iPad joining is not enabled.")

        # Do NOT trust X-Forwarded-Proto from arbitrary internet clients.
        # ASGI scope["scheme"] is safe only behind a correctly trusted
        # HTTPS-terminating proxy or native TLS ASGI server.
        if request.scope.get("scheme") != "https":
            raise HTTPException(status_code=426, detail="HTTPS is required.")

        # Client can request a join for an internal session ID only.
        # Reject any supplied identity/Zoom metadata, including JSON bodies.
        if await request.body():
            raise HTTPException(status_code=400, detail="Request body is not permitted.")

        authorization = request.headers.get("authorization", "")
        match = _BEARER.fullmatch(authorization)
        if match is None:
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Must be implemented by a verified faculty auth provider, never by
        # blindly decoding a JWT or trusting user-provided faculty IDs.
        try:
            faculty = verify_faculty_token(match.group(1))
        except Exception:
            # Avoid disclosing or logging user or token details.
            raise HTTPException(status_code=401, detail="Authentication required.") from None
        if not isinstance(faculty, AuthenticatedFaculty):
            raise HTTPException(
                status_code=401,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            ticket = join_service.issue_ticket(faculty, session_id)
        except JoinDenied:
            # Same generic error for unknown meetings and unauthorized faculty.
            raise HTTPException(status_code=403, detail="Meeting access denied.") from None

        # Do not return SDK Client Secret, Zoom host credentials, join URLs,
        # user records, assignment state, or server configuration.
        return JSONResponse(ticket.as_response())

    return app
