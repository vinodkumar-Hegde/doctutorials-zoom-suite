# Gate 3A — One-Channel Windows Zoom Plugin SDK Recording Feasibility

**Date:** 2026-11-14  
**Scope:** Zoom **Meetings only**, separate Basic Zoom sandbox and a Windows office workstation. **No webinars, production credentials, or four-channel changes.**

## Current state — incomplete by design

- Gate 2B local Basic sandbox read-only Meetings backend: **operator-confirmed PASS**, including 23/23 offline tests, authenticated list/detail, and unauthenticated HTTP 401.
- Gate 3A: Zoom Windows Plugin SDK **native IPC connection and recording controls NOT YET TESTED**. No custom recording executable is claimed to exist.
- A **read-only** Windows environment / SDK folder / finalized MP4 artifact probe has been committed in `backend/windows_recorder_probe.py` with 12 new mock/file tests. The repository now has **35** offline tests; the new 12 have **not** yet been run on operator Windows.
- **Do not infer** that a previously successful Zoom S2S OAuth token is sufficient for Plugin SDK authentication. This is a different app/authorization path.

## Source-verified Zoom prerequisites

Per Zoom's current official Windows Plugin SDK pages:

1. Windows Zoom Workplace **7.0.2 or higher**, using a supported, compatible Plugin SDK.
2. Visual Studio **2019 or later** with C++ build components for the SDK demo.
3. A Zoom Developer **General App** with Plugin SDK access, **not** a production Zoom tenant reconfiguration or a change to the existing S2S app.
4. Plugin connection OAuth token with `plugin_sdk:read:connection_meta` as documented by Zoom. The token goes into the **local demo**; never copy it into GitHub, chat, shell command history or screenshots.
5. Vendor SDK downloaded from **Zoom Marketplace → Developer → Created Apps → General App → Features → Access → Plugin SDK → Windows**. Keep the download and extracted binaries **outside the Git repository**.
6. The official demo is `demo/windows/PSDKTest/PSDKTest.sln` built `Release | x64`; it exercises `InitZMToolSuite`, Plugin SDK auth/IPC callbacks, meeting context and available recording capability/start tests.

The official demo description explicitly mentions **recording capability checks and start actions**. That is **not enough** to assert programmatic Stop/Pause/Resume, correct recording permission, conversion callbacks, or final MP4. Inspect the actual version's Plugin SDK C++ headers and demo controls before implementing custom recording commands. Meeting SDK recording-controller functions belong to a **different SDK** and must not be assumed present in Plugin SDK.

**Official pages (reviewed 2026-11-14):**
- Windows Plugin SDK prerequisites and download: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/
- Zoom-provided Windows demo: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/try-demo-app/
- Plugin SDK integration & scope: https://developers.zoom.us/docs/plugin-sdk/windows/integrate/
- Plugin SDK authentication & callbacks: https://developers.zoom.us/docs/plugin-sdk/windows/start-join-mtg-webinar/authentication/
- Plugin SDK Windows reference: https://marketplacefront.zoom.us/sdk/plugin/windows/index.html
- Plugin SDK specific errors: https://developers.zoom.us/docs/plugin-sdk/windows/error-codes/

## Stage 3A.1 — Run non-invasive readiness probe on Windows (next operator action)

From Windows PowerShell in the existing project directory:

    cd "$HOME\doctutorials-zoom-suite"
    git pull
    python -m unittest discover -s tests -v
    python -m backend.windows_recorder_probe --environment

Expected offline summary: **Ran 35 tests / OK** (23 previously operator-confirmed plus 12 new tests). **Not yet confirmed.**

The environment check only detects a likely Zoom executable in common installation locations; it does not extract credentials, inspect meetings, launch Zoom, or claim IPC is connected. A NOT FOUND result can occur with other Zoom installation layouts and does not establish Zoom is absent.

Check the actual Zoom Workplace version using **Zoom Workplace desktop application → profile/avatar → Help → About Zoom Workplace** (UI path can vary by version). Do not use the Chrome web meeting as evidence of a Windows client.

## Stage 3A.2 — Vendor SDK demo (after 3A.1)

- In the **separate free Zoom sandbox developer context**, create or select a dedicated **General App** for Plugin SDK access. Do not modify the production organization's developer apps or existing recording settings.
- Obtain the Windows SDK from the General App's Plugin SDK access section. The existing **S2S account-credentials tokens are not assumed to work for the Plugin SDK OAuth connection**. Use Zoom's documented OAuth authorization and appropriate scope. No secret values in GitHub/chat.
- Optional extraction check (only if SDK has been downloaded), pass the **actual** extracted `PSDKLibs` folder:

      python -m backend.windows_recorder_probe --sdk-dir "C:\path\to\PSDKLibs"

- Build the official `PSDKTest.sln` with Visual Studio (Release x64). Sign in to **Zoom Workplace Windows desktop** using the free Basic sandbox account, start its disposable scheduled **meeting** only, and authenticate the test SDK client.
- Record just these **non-secret** results: actual Workplace/Plugin SDK versions, IPC auth callback **PASS/FAIL**, meeting status **PASS/FAIL**, **local** recording capability check **PERMITTED/DENIED**, local **Start** **PASS/FAIL/UNAVAILABLE**, local **Stop** **PASS/FAIL/UNAVAILABLE**, Pause/Resume **PASS/FAIL/UNAVAILABLE**.
- A submitted SDK call or initial success code is not proof of ongoing recording. Watch relevant state/callbacks, allow Zoom conversion to complete, and verify a local MP4 independently.
- If a capability is missing, show **UNAVAILABLE** and stop. Do not build UI buttons that pretend to work. A manual host recording can be a separate baseline but does NOT pass the Plugin SDK remote-control acceptance gate.

## Stage 3A.3 — Verify one finalized local MP4, only after a recording exists

After Zoom finishes converting the local recording, **do not upload the recording**. Run:

    python -m backend.windows_recorder_probe --verify-mp4 "C:\actual\path\to\final-recording.mp4"

The probe is **read-only**: verifies file stays unchanged for 2 seconds and checks basic MP4 top-level `ftyp`, `mdat`, and `moov` boxes. It is **not a decoder or playback test**. Also play the complete recording locally and confirm audio, faculty video and shared screen. Do not publish paths or video content.

The probe never records, starts/joins meetings, connects IPC, or guarantees media content or conversion quality. It does not write, move, delete, upload, or archive the source MP4.

## Safety and acceptance gates

- [ ] 35/35 offline tests PASS (operator confirmation pending).
- [ ] Workstation actual Zoom Workplace version confirmed and compatible with vendor SDK.
- [ ] Dedicated sandbox Plugin SDK General App and correct OAuth authorization configured without changing production.
- [ ] Official PSDKTest demo built and IPC authorization callback PASS to the sandbox Windows Zoom Workplace client.
- [ ] One sandbox Zoom Meeting context/status observable.
- [ ] Local recording permission/capability verified.
- [ ] Local Start and Stop supported and confirmed by SDK/demo plus corresponding observable recording states.
- [ ] Pause/Resume explicitly determined supported or unsupported and independently tested if available.
- [ ] MP4 finalized, basic integrity probe PASS, complete local playback with proper audio/video/share.
- [ ] No webinar call, cloud-backup changes, tokens in repositories, or use of production host accounts.

**Gate 3A pass criteria:** One authorized **Windows Plugin SDK-controlled**, independent local Zoom Meeting recording with verified final MP4 and observed controls. **A manual MP4 alone does not pass this gate.** Four concurrent channels and the branded dashboard are later work.

## Future after Gate 3A proof

Write a native Windows SDK bridge (C++ adapter) using confirmed vendor header signatures, then add supervised one-channel command/state transport to the DocTutorials backend. Only enable each UI control if SDK permissions and callbacks substantiate it. Test two, then four isolated Windows recorder workers; implement NAS archival after verified conversion and checksum policy. If SDK recording controls prove insufficient, document the limitation and evaluate supported alternatives **before** choosing another recording architecture.
