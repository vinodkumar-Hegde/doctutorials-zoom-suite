# Stage 4B — First-Party Static Faculty Password (Zoom Basic Sandbox)

**Operator decision: 2026-11-15.** For initial testing, use a **fixed DocTutorials-managed password**, not Firebase, Google, Microsoft or another third-party login provider. This is a **single-sandbox-faculty prototype**, not a multi-user production account system.

## How it works

1. The operator privately chooses one persistent password for faculty ID `sandbox-faculty`. A local CLI prompts with hidden input; **never paste the password into ChatGPT, a Git commit, shell arguments or a screenshot**.
2. Backend creates a unique salted **scrypt** hash (N=2^17, r=8, p=1, 32-byte output) and saves a **mode-0600 private JSON file** by default at `~/.config/doctutorials/faculty-basic-sandbox.json`. The file contains a stable faculty ID, display name, active flag and password hash; **no plaintext password**.
3. When a properly secured HTTPS server is separately configured and the login feature is explicitly enabled, faculty signs in with faculty ID + their fixed password at `POST /api/faculty/login`:
   - JSON body contains exactly `facultyId` and `password`.
   - Correct credentials create a **new, unpredictable, 15-minute, in-memory bearer access token**; the password never becomes the bearer token. Token is different each login.
   - Responses: `accessToken`, `tokenType: Bearer`, `expiresAtEpoch`, with `Cache-Control: no-store, private`.
   - Wrong password, nonexistent faculty, inactive faculty return generic `401`. Five failed valid-format attempts within 15 minutes lock this one sandbox account for 15 minutes. Ingress per-IP and request-volume rate limits are still required.
4. iPad can call the existing HTTPS `POST /api/sessions/{session_id}/join/ipad` with this ephemeral bearer token. The server additionally checks **server-owned Zoom Basic sandbox assignment and session time window** before issuing a **participant-only** Meeting SDK JWT and join ticket.
5. `POST /api/faculty/logout` revokes the in-memory bearer token. Token expiry and process restarts also invalidate sessions.
6. The static faculty login password **is NOT a Zoom meeting passcode, SDK Client Secret or host password**. Zoom SDK credentials stay on trusted backend only.

**All HTTP routes are OFF by default** via `enable_password_login_api=False` and `enable_ipad_join_api=False`. No listener, TLS endpoint, sample password, fake production faculty account or auto-join UI has been enabled in this commit. Local password authentication must be accompanied by trusted HTTPS, secret manager, server-owned assignment storage and ingress protections before live use.

## Code

- `backend/faculty_password_auth.py` — salted scrypt fixed-password storage, one sandbox principal, 15-minute opaque token, session expiry/revocation, login throttling and private operator setup CLI.
- `backend/faculty_password_http.py` — default-disabled first-party HTTPS login/logout routes integrated with the existing authorized iPad join ticket app.
- `tests/test_faculty_password_auth.py` — **28 offline tests committed; OPERATOR EXECUTION PENDING**. Includes hash correctness, randomness, private-file protections, wrong identity/password, inactivity, lockout, expiry, logout, simulated HTTPS login → sandbox participant join, untrusted host and no secret leaks.
- `ipad/DocTutorialsScreenShare/SDKApp/HTTPSFacultyPasswordLoginClient.swift` — first-party HTTPS login/logout transport, ephemeral URLSession, redirect rejection, no local password persistence. **Build not yet Mac-verified** and **not connected to existing disabled Join button**.
- Existing `backend/ipad_join_authorization.py`, `backend/ipad_join_http.py` and `SDKApp/HTTPSFacultyJoinTicketClient.swift` remain unchanged.

## Set your permanent sandbox password privately on Mac

This does not start a Zoom meeting, authenticate an iPad, or expose a server.

~~~bash
cd ~/doctutorials-zoom-suite
git pull

python3 -m backend.faculty_password_auth setup \
  --faculty-id sandbox-faculty \
  --display-name "Sandbox Faculty"
~~~

The Terminal will request a **16–128 character** password and ask you to repeat it, without echoing input. Use a long unique random password or passphrase. The password remains the same for subsequent logins until deliberately changed. The hash file is created at `~/.config/doctutorials/faculty-basic-sandbox.json` with private permissions and is **never committed**. If setup reports the file already exists, do not overwrite it blindly; first plan a rotation and invalidate active server sessions. If the Mac is only a development machine, provision the password hash privately on the *eventual* trusted backend too.

## Mac offline validation (no Zoom credentials, no public server)

Uses the same isolated Python venv prepared for the previous 19 HTTP tests.

~~~bash
cd ~/doctutorials-zoom-suite
"$HOME/.venvs/doctutorials-ipad-api/bin/python" -m unittest discover \
  -s tests -p 'test_faculty_password_auth.py' -v
~~~

Expected **28 tests, zero failures / OK**; **not yet confirmed**. Tests use a clearly fake password in code and a test-only in-memory faculty assignment. They make no live Zoom calls.

Then check the Swift login transport compiles under the SDK project:

~~~bash
cd ~/doctutorials-zoom-suite/ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
~~~

Select iPad (A16) and use **Cmd+B**, then **Cmd+U**. The existing five policy tests must remain green; this test does not prove live sign-in or SDK meeting connection.

## Security and scope before any live deployment

- This is **one operator-managed Basic sandbox account** only. It does not establish real multi-faculty identity, enrollment or student access. **Never use a single password shared by multiple instructors** for real operations; add individually provisioned users and centrally managed session/revocation storage later.
- Bind any future API listener to genuine HTTPS with valid certificate, trusted proxy scheme/host, ingress throttling and request-size limits. IP rate limiting and app server lockout defend against guessing; five-attempt lockout alone is insufficient. Prevent passwords, tokens and meeting IDs from appearing in request/body logs.
- The app is **disabled by default**; there is no live HTTPS server or configured sandbox faculty assignment database. A successful offline login simulation is **not** a real iPad sign-in or Zoom participant join.
- Hash config belongs in operator-controlled protected local/server storage. Back it up securely; rotate password by provisioning a NEW hash and restarting the single-instance sandbox backend to discard sessions. **Never use SDK secrets, host credentials, Zoom account passwords or a single static bearer token** as the faculty login password.
- Static passwords need appropriate device security, rate limits and periodic credential compromise review; stronger factors can be introduced later without requiring a third-party login vendor.

## References

- OWASP password storage (salted slow hashes and scrypt minimum N=2^17, r=8, p=1): https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP authentication (generic denial messages and brute-force defenses): https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- HTTPS and trusted proxy deployment: https://fastapi.tiangolo.com/deployment/https/
