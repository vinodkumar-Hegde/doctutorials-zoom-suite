# Stage 4B — First Real Faculty Login and Zoom Basic Meeting Join (Mac + iPad Simulator)

**Goal:** Stop iterating on disconnected shells. Start the actual first-party faculty login API on the operator's **Mac localhost**, sign in from the **SDK-enabled iPad Simulator UI**, and request an authorized participant join of an actual existing **Zoom Basic sandbox Meeting**. Keep Windows recording, webinars, production hosts and ReplayKit broadcast out of this first-live-join milestone.

## Committed implementation — NOT YET OPERATOR-BUILT OR LIVE-VERIFIED

1. `SDKApp/FacultySandboxMeetingView.swift` is the **new SDK-only launch UI**: local HTTPS backend URL, static faculty ID/password, Sign in/out, internal assigned session ID, and authorized Join button. The SDK-only `project-sdk.yml` sets `ZOOM_MEETING_SDK_ENABLED`; the default UI-only `project.yml` remains unchanged. App entry point switches to the real faculty view only for SDK variant.
2. Login calls existing `HTTPSFacultyPasswordLoginClient` with the operator's static sandbox password; no password stored in the iPad app. The backend issues a 15-minute opaque bearer token after actual password verification. The Join action passes that temporary token and an internal DocTutorials session ID to existing `HTTPSFacultyJoinTicketClient`, which rejects untrusted HTTP and redirects. Server decides actual authorized faculty/meeting/time and signs **participant-only SDK JWT role=0**. On accepted ticket, view calls `ZoomMeetingJoinAdapter.joinAssignedMeeting`. **Only the SDK callback `.inMeeting` means connected**.
3. `backend/local_ipad_sandbox_server.py`: a real, independently runnable **127.0.0.1-only, TLS-only** first-party login + join-ticket FastAPI composition, using the already-provisioned faculty password hash, a private server-owned Basic sandbox meeting assignment file, and **separate SDK General App Client ID/Secret** supplied interactively (hidden Terminal). Does not use production credentials. Server is not public, does not grant host roles or bypass waiting rooms.
4. `scripts/setup_local_simulator_https.sh`: generates a short-lived private localhost TLS certificate/CA under `~/.config/doctutorials/localhost-tls`, then installs the temporary CA **only in booted iPad Simulator keychain** with `xcrun simctl keychain booted add-root-cert`. Do NOT import this test CA into production, staff devices or your Mac-wide system trust store.
5. `scripts/run_local_sandbox_demo.sh`: one terminal entry point: create simulator TLS, securely prompt for sandbox meeting number/passcode if missing, regenerate/open real Xcode project, privately prompt for Meeting SDK General App ID/Secret, run HTTPS API **on loopback only**. No test passwords or real credentials in code/Git.
6. `tests/test_local_ipad_sandbox_server.py`: six additional offline tests for password-to-authorized-participant ticket, missing bearer, private assignment mode, invalid environment and wrong faculty. **Not yet executed on operator Mac.** The previous 28/28 password auth, 19/19 HTTP API, 12/12 assignment, 8/8 backend JWT and 5/5 SDK-XCTest passed BEFORE the new local-server/UI changes.

### Fastest operator trial

**Prerequisite:** iPad (A16) Simulator is booted; your private `sandbox-faculty` password hash was already successfully created. Know the **existing Basic sandbox Meeting number/passcode** and the **Meeting SDK General App** Client ID/Secret, but **do not share them in chat or shell command arguments**. This must be a meeting owned by the same Zoom Basic sandbox account as the Meeting SDK app. Ideally have that meeting **started as host on laptop** to allow the iPad participant to join.

Mac Terminal:

```bash
cd ~/doctutorials-zoom-suite
git pull
bash ipad/DocTutorialsScreenShare/scripts/run_local_sandbox_demo.sh
```

The script may request the **meeting number**, **meeting passcode**, then **SDK General App Client ID and Secret** through hidden Terminal prompts. **This terminal stays occupied serving HTTPS**; leave it running while testing, stop with Ctrl+C. It will print the local server URL and UI inputs, not credentials. If it reports TLS/Simulator trust error, send the error **without secrets**. Local TLS root trust was added to the booted Simulator ONLY; it may need reinstallation after resetting the simulator.

In Xcode (opened by the script):
- Choose `DocTutorialsScreenShare` → **iPad (A16)** and press **Cmd+R**. This is the new **Faculty iPad Meeting** screen, not the old “Preview sample class” shell.
- **Backend URL:** `https://localhost:8443`
- **Faculty ID:** `sandbox-faculty`
- **Password:** your previously set private static faculty password. Tap **Sign in to DocTutorials**. Expected genuine server result: **Signed in to DocTutorials (sandbox)**.
- **Assigned DocTutorials session ID:** `ipad-sandbox-class` (NOT Zoom Meeting number). Tap **Join assigned meeting**. Wait for Zoom's *observed* SDK callback and report whether the screen shows **Connected to assigned Zoom meeting**, waiting or failed. These status labels MUST NOT be interpreted as success until observed; actual connection remains unverified.
- iPad microphone/video are requested OFF; faculty laptop runs Zoom host camera/audio. Waiting room/Zoom guest settings can still gate entry. **Do not attempt to broadcast**: ReplayKit extension and share entitlement are not wired, and the privacy gate stays fail-closed.

### Security boundaries

- **No external login platform.** This is one operator-created sandbox faculty password, protected locally as a slow salted hash, not an iPad-embedded password. Avoid copying the password/hash, SDK ID/Secret, Zoom meeting passcode or token into any screenshot/chat/GitHub issue.
- Backend listens only on **127.0.0.1:8443** and cannot serve physical iPads. Before any real-device or public deployment, provide a trusted HTTPS hostname, per-IP ingress throttling, secret vault, account controls, reliable session storage, and server-owned scheduled session assignment. Do NOT expose this localhost service via a tunnel or reverse proxy; it is a limited development pilot.
- Sandbox assignment is private **0600** JSON under `~/.config/doctutorials/ipad-basic-assignment.json`, linked only to `sandbox-faculty`; for first test its time window is about one hour and is NOT silently renewed. To change an expired/incorrect assignment, securely archive or remove this private file on the operator Mac and rerun the private setup. Never check the file into GitHub.
- SDK JWT participant role=0 does not grant Zoom host privileges or bypass waiting rooms. iPad “connected” may still require host admission.
- This milestone does not include an authenticated assigned-class list; for the single sandbox test the operator enters the harmless **internal session ID**, while the backend owns all meeting-specific information and verifies it.

**Troubleshooting:** If the app does not compile, report the **first red Swift compiler error** from Cmd+R; do not report only non-blocking simulator networking/PointerUI orientation warnings. If backend startup fails, report its first error without copying private values. If login returns 401 check static password and account lockout; if 403 on join check assignment/session ID and eligibility time; if 426 verify HTTPS; if connection is waiting, check host and Zoom waiting-room permission.

## Acceptance criteria

- [ ] New faculty login/Join screen visually renders in **SDK-enabled** iPad Simulator (not yet verified after commit).
- [ ] Local TLS certificate trusted by the booted iPad Simulator, HTTPS server listening **127.0.0.1**, not external interfaces (pending).
- [ ] Real static faculty password login in Simulator returns usable ephemeral session token (pending).
- [ ] First-party backend approves one correct assigned Basic sandbox meeting and denies wrong/expired faculty/session (offline prior domain tests passed; **live proof pending**).
- [ ] Zoom Meeting SDK authorizes and issues a join request; a real `.inMeeting` callback is observed and another sandbox attendee sees iPad participant (pending).
- [ ] Real iPad ReplayKit screen broadcast to Goodnotes attendee (**separate later gate**, not supported yet).

## Validation without live Zoom credentials (optional troubleshooting)

```bash
cd ~/doctutorials-zoom-suite
"$HOME/.venvs/doctutorials-ipad-api/bin/python" -m unittest discover -s tests -p 'test_local_ipad_sandbox_server.py' -v
```

Six cases expected but **never claim them passed until operator runs them**. Live simulator sign-in and join is the priority now.
