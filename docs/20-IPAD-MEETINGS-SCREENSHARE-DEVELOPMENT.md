# Active Stage 4A — DocTutorials Faculty iPad Screen Sharing (Meetings First)

**Operator priority change:** 2026-11-14. **Build iPad screen-sharing app now; move Windows local recorder/control center to the LAST development phase**. Keep Zoom **Meetings only** in the separate free Basic sandbox until that scope is proven. No webinar API or production host modifications.

## Intended faculty experience

1. Sign in with DocTutorials credentials to see only assigned classes (backend/auth integration pending).
2. Tap an assigned **Zoom Meeting**; join as authorized participant without exposing any of the four production Zoom host credentials.
3. Keep iPad microphone and video muted/off by default; faculty laptop supplies live camera and voice.
4. Check a privacy warning, then explicitly use Apple's ReplayKit screen broadcast picker and confirmation.
5. Leave DocTutorials app to write in Goodnotes/Notability, and see full screen content on a second meeting participant's device.
6. Return to DocTutorials, stop via the OS broadcast control, exit the meeting; clearly report any disconnections.

The OS broadcast is **device-wide**, not Goodnotes-only. Faculty must enable Focus/Do Not Disturb and avoid opening private content. Apple's user confirmation cannot be bypassed.

## Work actually committed (2026-11-14)

- [x] SwiftUI **UI-only** shell in `ipad/DocTutorialsScreenShare/App/` with a sample lecture preview, meeting/share not-connected states, privacy acknowledgement, screen share description and explicit development status.
- [x] Pure Swift `ScreenSharePolicy` that exposes the picker only if **(a) joined meeting observed + (b) user privacy acknowledgment + (c) Zoom sharing entitlement observed**.
- [x] Five Xcode XCTest policy tests in `ipad/DocTutorialsScreenShare/Tests/`. **Not run**, because no Mac Xcode invocation has been performed.
- [x] XcodeGen `project.yml` for an iPad-only shell app and unit-test target. **Not generated/compiled/signed yet**.
- [x] Vendor-compatible **staged source template** `BroadcastExtension-SDK-Template/SampleHandler.swift` with ReplayKit callbacks delegated to `MobileRTCScreenShareService`, deliberately excluded from app build until Meeting SDK distribution and proper Broadcast Upload Extension target are configured.
- [ ] Xcode-generated iPad app builds and launches on a real device (operator evidence pending).
- [ ] Create/select a dedicated Zoom Meeting SDK **General App** for the **Basic sandbox developer account**, separate from Server-to-Server OAuth and Windows Plugin SDK.
- [ ] Backend authentication, faculty assignment and **short-lived Meeting SDK JWT** signed on the server; no SDK secret in app.
- [ ] Actual Zoom Meeting SDK iOS initialization and authenticated non-host participant join; callbacks establish real `inMeeting` state.
- [ ] Verify current cross-account review/ZAK/OBF requirements before ever joining paid-tenant sessions (not part of sandbox PoC).
- [ ] Apple App Group entitlement created and matched between main and Broadcast Upload Extension; valid Apple signing/team; Zoom-specific frameworks configured per version.
- [ ] Real ReplayKit full-device broadcast from iPad to a **second** joined meeting client, including Goodnotes handwriting; independent recipient confirms video frames and share continuity.
- [ ] Interruption/stop/rejoin, muting, share entitlement, privacy notification and foreground/background handling tests.
- [ ] No webinars or four-channel Windows recorder work during this stage.

**Important:** Source files and a design scaffold are **not** a working Zoom iPad sharing application. There is no live SDK join adapter, real broadcast extension target, SDK library, bundle signing, or TestFlight build yet.

## Required developer setup

A **Mac with Xcode** is required to compile and sign an iOS/iPadOS app; a Windows Visual Studio installation cannot compile native iPad apps. For Zoom Meeting SDK **7.0.0+**, Zoom currently documents **Xcode 26+** and a real 64-bit iPad on iPadOS 15+. Our UI shell deployment target is iPadOS 16+, and later SDK compatibility must be checked at integration time.

The checked-in `project.yml` uses [XcodeGen](https://github.com/yonaskolb/XcodeGen) to generate an Xcode project. On the **Mac** (after installing Xcode, command-line tools, XcodeGen and getting a clone of this repo):

```sh
cd doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
xcodegen generate
open DocTutorialsScreenShare.xcodeproj
```

Select the `DocTutorialsScreenShare` scheme. Change `PRODUCT_BUNDLE_IDENTIFIER` to an identifier you control if Apple's signing setup requires it. Configure the correct Apple Development Team under Signing & Capabilities. For the **UI-only shell**, no Zoom secrets or SDK download is needed. On a connected iPad choose the iPad run destination and click Run. The screen should explicitly say there is no Zoom connection and should NOT enable Join or Share.

Run the scheme's **Test** action (Cmd+U) in Xcode; expect **five** policy tests. This has **not** yet been operator-confirmed.

## Next: Meetings SDK and ReplayKit integration (behind proof gates)

1. Create/select sandbox-associated **General App → Meeting SDK**. Never use credentials from the existing S2S app as a Meeting SDK secret; do not place any credentials in GitHub, .swift source or a chat screenshot.
2. Match a supported iOS Meeting SDK release with Mac Xcode/iPadOS version. Download the **vendor SDK and sample** through official Zoom distribution; do **not** commit proprietary SDK binaries.
3. Backend generates time-limited Meeting SDK JWT from securely stored Meeting SDK client ID/secret, only after checking authorized faculty/session. Within the app owner's developer account a participant may join with JWT alone. **Outside** that account, current Zoom policy requires reviewed app and ZAK or OBF authorization; do not promise cross-account joining without proof.
4. Implement SDK initialization, real `MobileRTCMeetingService` join with microphone/video muted by default, and callbacks `onMeetingStateChange` / `onMeetingError`. No hardcoded host credentials and no fabricated “connected” state.
5. Create **Broadcast Upload Extension** in Xcode; add `MobileRTCScreenShare.framework` to **extension only**, `MobileRTC.framework` to main app, and Apple frameworks/Swift bridging header as required by the exact SDK. Use the staged `SampleHandler.swift` code only after confirming version-specific signatures. Enable same **registered App Group** on app and extension; initialize SDK `appGroupId` and `screenShareService.appGroup`; link `-lc++` in extension. Configure Audio/AirPlay/PiP background modes per Zoom's full-device share guidance. Do not make up App Group or Apple Team IDs.
6. Only make the ReplayKit broadcast control accessible when SDK confirms a joined meeting and host-authorized share. Apple system confirmation remains mandatory, and OS-level broadcast starting does not prove the meeting is receiving media.
7. Test with one sandbox meeting, faculty laptop audio/video and a second attendee for observation. Switch to Goodnotes, write, check audio/visual content at receiver, stop, verify stop. Test reconnect with explicit restart.
8. No webinar implementation until Meetings integration passes and the operator explicitly authorizes that phase.

### Known caveats

- Zoom's iOS Meeting SDK ReplayKit sharing guide says full-device share uses a broadcast extension and `MobileRTCScreenShare`, unlike single-view sharing. iOS broadcasts can be started outside a Zoom meeting, in which case no attendees receive media; therefore observed meeting/share callbacks are required for an actual success state.
- Apple currently marks `RPSystemBroadcastPickerView` deprecated in its online documentation, suggesting ScreenCaptureKit alternatives. Zoom's current iOS Meeting SDK guide still documents ReplayKit broadcast picking. Confirm platform/SDK guidance for the targeted iPadOS version before release; the existing preview does not expose the picker.
- App Group and Broadcast extension must use matching registered IDs and authorized signing. A third-party notes app may display sensitive notifications or content.
- **No app has been compiled or tested on an iPad in this session.** All Windows backend passes remain valid; the 35 Python tests are unrelated to iPad XCTest.

## Official sources checked 2026-11-14

- Zoom iOS Meeting SDK setup / Xcode compatibility: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/
- Zoom iOS Meeting SDK integration: https://developers.zoom.us/docs/meeting-sdk/ios/integrate/
- Zoom iOS Meeting SDK ReplayKit full-device broadcasting: https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/screen-share/
- iOS Meeting SDK join code and callbacks: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- Zoom Meeting SDK authentication/JWT and external-account review: https://developers.zoom.us/docs/meeting-sdk/auth/
- Apple ReplayKit picker user confirmation: https://developer.apple.com/documentation/replaykit/rpsystembroadcastpickerview

## Mac Xcode prerequisite now confirmed (operator report 2026-11-14)
The operator successfully ran `xcode-select -p` and `xcodebuild -version`: `/Applications/Xcode.app/Contents/Developer`, **Xcode 27.2 (27B52)**. Full Xcode is installed and the active command-line developer directory is correct. Earlier errors are superseded. Git/Homebrew/XcodeGen/repository presence on Mac, Xcode project generation, compilation, signing and real iPad tests still await verification. Do not claim an app was built.

## 2026-11-15 — Mac GitHub clone verified (operator report)
- The private repository was cloned successfully at `~/doctutorials-zoom-suite` on Mac. `git status` showed branch `main`, up to date with `origin/main`, clean working tree.
- Git 2.54.0, Homebrew 7.0.13 and Xcode 27.2 were already confirmed. Next step is installing/checking XcodeGen via `brew install xcodegen`, generating `ipad/DocTutorialsScreenShare/project.yml` with `xcodegen generate`, and opening the generated project.
- The SwiftUI shell has **not been compiled or tested yet**. The join and broadcast controls remain intentionally inactive and real Zoom/ReplayKit SDK integration is a later milestone.

## 2026-11-15 — Project generated on operator's Mac
- **XcodeGen 2.46.0 installed via Homebrew: PASS**.
- **Xcode project generation: PASS**, confirmed output `Created project at .../ipad/DocTutorialsScreenShare/DocTutorialsScreenShare.xcodeproj`.
- **App build, iPad Simulator run, XCTest 5/5: PENDING**. Xcode opening and any iPad hardware testing have not yet been confirmed.
- Next: open project in Xcode, select the DocTutorialsScreenShare scheme + iPad Simulator, Cmd+R to build/run. Then Cmd+U to execute five policy tests. Report first red build error if any; do not make feature acceptance claims from project generation alone.

## 2026-11-15 — iPad Simulator UI launched: PASS
- Operator screenshot confirms the **DocTutorialsScreenShare** SwiftUI app running on an **iPad (A16) iPadOS 27.2 Simulator**.
- Observed UI: faculty screen-sharing header; no real class loaded, optional sample class; disconnected Zoom Meeting state and disabled Join button; disabled screen broadcast; privacy acknowledgement toggle ON; explicit "Development preview — no meeting is joined or broadcast" label.
- This passes **UI-only simulator launch**, not Zoom join, actual ReplayKit sharing, physical iPad or end-to-end integration.
- Next: select `DocTutorialsScreenShare` scheme in Xcode and run `Cmd+U` to execute five screen-share policy XCTest cases. **5/5 not yet confirmed**.

## 2026-11-15 — 5/5 SwiftUI policy tests PASSED
- Operator screenshot and raw XCTest log confirm all **five `ScreenSharePolicyTests` passed with zero failures**, Test Suite 'All tests' PASSED on iPad (A16) simulator / iPadOS 27.2.
- Tests cover fail-closed disconnected/absent privacy acknowledgment/absent Zoom share permission and valid all-three-gate case; this is UI-policy evidence only.
- Simulator emitted **non-blocking** launch measurements, pointer UI telemetry and advisory that Info.plist should support all orientations; include orientation key review before release. These warnings do not demonstrate an SDK crash or test failure.
- Next Zoom Developer prerequisite (meeting-only Basic sandbox): sign in to [Zoom Marketplace](https://marketplace.zoom.us/), open developer **Created Apps → Build App → General App**, go to **Features → Embed** and enable **Meeting SDK**, then download the iOS SDK from app setup. Keep distinct from the existing Server-to-Server OAuth backend app and any Windows Plugin SDK app. **Do not disclose or commit Client ID/Secret/JWT**. Confirmation needed: app created, Meeting SDK feature ON, iOS package available, with no credentials provided.
- Continue to require backend-generated short-lived Meeting SDK JWT and real meeting-join/permission callbacks before enabling Share. No webinar or production host changes.

## 2026-11-15 — Zoom Meeting SDK app enabled; SDK archive downloaded (operator report)
- Operator reports **DocTutorials-iPad General App created** and **Meeting SDK feature enabled**, with download placed in **Mac Downloads**. Actual archive file name, SDK version and folder contents **not yet inspected**; neither the Zoom framework nor JWT backend are wired into our Xcode app.
- Official [Zoom iOS Meeting SDK download and file verification](https://developers.zoom.us/docs/meeting-sdk/ios/get-started/) specifies archive contents: `version.txt`, `lib/`, `MobileRTCSample/`, `README.md`. Current [Zoom iOS integration guide](https://developers.zoom.us/docs/meeting-sdk/ios/integrate/) lists `lib/MobileRTC.xcframework`, `lib/MobileRTCResources.bundle`, and optional `lib/MobileRTCScreenShare.xcframework` for ReplayKit (and `zoomcml.xcframework` for optional features).
- **Next task on Mac:** locate the downloaded Zoom iOS SDK ZIP and extract it **outside the repository**; check the exact SDK release in `version.txt`, plus actual available framework names and paths. Never copy SDK credential values or whole proprietary SDK archives into GitHub.
- Zoom's currently published iOS compatibility list cites supported maximum iOS system **26** for Meeting SDK 6.0.2+ despite operator simulator showing iPadOS **27.2**. Treat iPadOS 27 support as **not yet documented/validated**; prefer a supported physical device and check release notes for downloaded SDK compatibility. UI-only Xcode simulator tests passing are not proof of Zoom Meeting SDK compatibility.
- Next after checking SDK files: link `MobileRTC.xcframework` and `MobileRTCResources.bundle` to main iPad app, then connect Meeting SDK authentication through a backend-issued time-limited JWT. The screen-share XCFramework and dedicated ReplayKit Broadcast Upload Extension are a separate step and require a registered App Group, identical in app and extension.

## 2026-11-15 — Downloaded iOS SDK ZIP located in Mac Downloads
- Mac Downloads contains vendor ZIP named `zoom-sdk-ios-7.2.5.40220.zip` (operator-confirmed ~187MB). Previous framework search was empty because package has not been extracted. Exact content/version still require inspection; do not treat ZIP name as verified SDK version.
- Next: `mkdir -p ~/Downloads/DocTutorialsZoomSDK && ditto -x -k ~/Downloads/zoom-sdk-ios-7.2.5.40220.zip ~/Downloads/DocTutorialsZoomSDK`, then locate `version.txt`, `MobileRTC.xcframework`, `MobileRTCResources.bundle` and `MobileRTCScreenShare.xcframework`. Keep SDK binaries outside Git; SDK integration in Xcode has not yet occurred.

## 2026-11-15 — Vendor SDK extracted; main app linkage prepared
Operator confirmed downloaded Zoom SDK ZIP was extracted under `~/Downloads/DocTutorialsZoomSDK` and all four required paths exist:
- `version.txt`
- `lib/MobileRTC.xcframework`
- `lib/MobileRTCResources.bundle`
- `lib/MobileRTCScreenShare.xcframework`

The actual `version.txt` contents have **not yet** been reported; do not equate ZIP name with verified SDK internal version. Our new optional `project-sdk.yml` supplements the known-working UI-only `project.yml`; it links `MobileRTC.xcframework` with embedding and signing and copies `MobileRTCResources.bundle` in the **main app only**. The future `MobileRTCScreenShare.xcframework` requires its own Apple Broadcast Upload Extension and matching App Group; it is deliberately **not** linked to the main app. The staged handler remains excluded.

**Next commands (on the Mac):**

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
bash scripts/prepare_zoom_sdk.sh
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
```

The preparation script checks files including `version.txt`, reports its first line, and creates `vendor/ZoomMeetingSDK` as a Git-ignored **symlink to the extracted SDK in Downloads**. It does not copy, upload or modify Zoom frameworks. `xcodegen generate --spec project-sdk.yml` replaces the ignored, locally generated Xcode project with the SDK-linkage variant. If generation/build fails, return to the proven UI-only config using `xcodegen generate --spec project.yml`. Neither generated variant has yet proved an actual SDK join.

In Xcode, inspect the app target → General → Frameworks, Libraries and Embedded Content: **MobileRTC = Embed & Sign**. Under Build Phases → Copy Bundle Resources: **MobileRTCResources.bundle**. No `MobileRTCScreenShare` in the main app target. Next verify build only on simulator before adding SDK authentication. Current official Zoom documentation supports up to iOS 26; operator simulator is iPadOS 27.2, so compatibility must be determined empirically or from updated Zoom release notes before declaring SDK runtime support.

Official: https://developers.zoom.us/docs/meeting-sdk/ios/integrate/ and https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/ios-screen-share-trouble-tips/; XcodeGen spec https://yonaskolb.github.io/XcodeGen/Docs/ProjectSpec.html

## 2026-11-15 — SDK framework linking configuration generated successfully
Operator Terminal result:
- `SDK framework paths: VERIFIED`
- `SDK version.txt: v7.2.5.40220`
- `Optional zoomcml XCFramework: FOUND`
- `Local vendor symlink: READY (ignored by Git)`
- `xcodegen generate --spec project-sdk.yml` → `Created project at .../DocTutorialsScreenShare.xcodeproj`

**Passed:** vendor SDK local file check, opt-in XcodeGen project generation. **Pending:** actual Xcode compile/link to iPad Simulator, app launch with SDK-linked build, real JWT authentication, meeting join/callbacks, and ReplayKit Broadcast Upload Extension. The Xcode project generation alone does not establish SDK binary compatibility.

Next operator step: open the generated Xcode project, select **DocTutorialsScreenShare / iPad (A16) Simulator**, press **Cmd+B**. Collect the first red error if compilation fails; otherwise confirm Build Succeeded. Do not need Zoom OAuth credentials for the SDK framework-only build.

## 2026-11-15 — Stage 4B: backend JWT signer and iOS meeting-join adapter staged
Operator reports `Cmd+B` for the **SDK-linked 7.2.5.40220 app PASSED** before the Stage 4B source changes below. **This does NOT prove a Zoom meeting was joined.**

New commits:
- `SDKApp/ZoomMeetingJoinAdapter.swift`: Stage 4B SDK adapter using official SDK init/auth and meeting join APIs; receives a transient, backend-authorized meeting ticket containing a participant display name, meeting number/passcode and short-lived Meeting SDK JWT. Audio and video are OFF by default. `.inMeeting` only comes from `onMeetingStateChange`; a return value of `.success` from the join call alone is not treated as connected. Waiting room and reconnecting are not joined. ReplayKit sharing remains **disabled**, because permission has not been observed. This source is intentionally **NOT connected to the SwiftUI Join button**: authenticated faculty login, verified assigned session and a secure HTTPS API must exist first.
- `project-sdk.yml` now includes `SDKApp` as a source directory only in the SDK configuration; original `project.yml` UI shell preserved.
- `backend/ipad_sdk_jwt.py`: **backend-only** Meeting SDK participant JWT HS256 signer, with App Client ID/Secret from backend secret store (NOT the Server-to-Server OAuth app). `appKey`, `iat`, `exp`, `tokenExp` are Zoom native requirements; also includes `mn`, `role=0`. TTL bounds 1800–7200 seconds.
- `tests/test_ipad_sdk_jwt.py`: 8 offline JWT correctness and invalid-input tests; **8/8 PASS in assistant's local Python environment**. These are not a live Zoom authorization or Mac SDK test.
- Swift syntax was parsed using the assistant's Linux Swift compiler. **Actual Xcode compilation against SDK 7.2.5 is pending operator run.**

**Next Mac validation:**

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
```

Select DocTutorialsScreenShare and iPad (A16), then **Cmd+B** for the first compilation of the adapter; **Cmd+U** to ensure existing five policy tests still pass.

Run newly added backend JWT tests separately (no Zoom credentials):

```bash
cd ~/doctutorials-zoom-suite
python3 -m unittest discover -s tests -p 'test_ipad_sdk_jwt.py' -v
```

**Next integration blocker after compile:** a backend HTTPS endpoint `POST /api/sessions/{id}/join/ipad` must authenticate a DocTutorials faculty identity, verify the assignment and authorized meeting, securely retrieve the sandbox Meeting SDK Client ID/Secret, generate JWT server-side, and respond with the ephemeral join ticket. The current Windows localhost-only FastAPI read service is NOT a safe/sufficient faculty HTTPS server and MUST NOT be exposed publicly or mistaken for this endpoint. No production Zoom settings or tokens altered.

References: https://developers.zoom.us/docs/meeting-sdk/ios/build-an-app/implement-features/ ; https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/ ; https://developers.zoom.us/docs/meeting-sdk/auth/ .

## 2026-11-15 — Fix staged for `dyld: Library not loaded: @rpath/zoomcml.framework/zoomcml`
First launch/test of newly generated SDK-enabled Stage 4B adapter hit an **Xcode Simulator dyld launch abort** because `MobileRTC.framework` dynamically references `zoomcml.framework`, which was not embedded in the app. This does **not** demonstrate a bug in the join adapter or failure in its policy tests; XCTest could not launch. Earlier SDK-linked **Cmd+B** success remains a compile/link result, not a runtime test.

**Committed fix, awaiting Mac retest:**
- `project-sdk.yml`: add `vendor/ZoomMeetingSDK/lib/zoomcml.xcframework` to the app's dependencies with `embed: true`, `codeSign: true`. Keep existing `MobileRTC.xcframework` Embed & Sign and `MobileRTCResources.bundle` Copy Bundle Resources. The future `MobileRTCScreenShare.xcframework` still belongs **only** to the ReplayKit Broadcast Upload Extension and is not needed here.
- `scripts/prepare_zoom_sdk.sh`: fail closed unless the local Zoom distribution includes `lib/zoomcml.xcframework` (operator previously confirmed it does).
- No changes to `project.yml` (UI-only known-good app) or host credentials.

Mac commands:

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
bash scripts/prepare_zoom_sdk.sh
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
```

Then select **DocTutorialsScreenShare → iPad (A16)**. Inspect app target → **General → Frameworks, Libraries, and Embedded Content**: `MobileRTC` = **Embed & Sign**, `zoomcml` = **Embed & Sign**. Perform **Product → Clean Build Folder (Shift+Cmd+K)** followed by **Cmd+U** and **Cmd+R**. If green tests and actual simulator launch both succeed, record separately. No real Zoom authentication, backend issuance, meeting join, or ReplayKit broadcast yet.

Sources: https://developers.zoom.us/docs/meeting-sdk/ios/integrate/ ; https://devforum.zoom.us/t/is-the-ios-meeting-sdk-still-actively-supported/147169 ; https://developer.apple.com/documentation/xcode/addressing-missing-framework-crashes .

## 2026-11-15 — Same dyld runtime error repeats; verify generated Xcode project
The operator again reported `@rpath/zoomcml.framework/zoomcml` missing, referenced by `MobileRTC.framework` in simulator products, following the previous commit to embed `zoomcml`. No command output was included to confirm that the updated `project-sdk.yml` was pulled and regenerated, or that the app target actually embeds `zoomcml.framework`. Treat the fix as **NOT VERIFIED**, not as a successful SDK runtime integration.

Do not add more blind build-setting changes until local state is known. Focused Mac diagnostics:

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
bash scripts/prepare_zoom_sdk.sh
xcodegen generate --spec project-sdk.yml
grep -n "zoomcml" DocTutorialsScreenShare.xcodeproj/project.pbxproj
find vendor/ZoomMeetingSDK/lib/zoomcml.xcframework -name "zoomcml.framework" -print
```

Next, open generated Xcode project; select **the app target**, not the top-level project or test target; inspect General → Frameworks, Libraries and Embedded Content and Build Phases → Embed Frameworks. **MobileRTC** and **zoomcml** must appear as embedded-and-signed dependencies. After a fresh clean/build/run, inspect `.../Build/Products/Debug-iphonesimulator/DocTutorialsScreenShare.app/Frameworks/zoomcml.framework`. If project references exist but build output is still missing, investigate Xcode target copy phase/build failures and XCFramework selected platform slice; if no project references, investigate XcodeGen generation/spec usage. A simulator code-sign/restriction warning would be a *different* error. Keep credentials out of logs.


## 2026-11-15 — Generated Xcode project DOES link and embed zoomcml (operator verified)
Operator's `grep -n zoomcml DocTutorialsScreenShare.xcodeproj/project.pbxproj` shows:
- `zoomcml.xcframework in Embed Frameworks` with `CodeSignOnCopy, RemoveHeadersOnCopy`
- `zoomcml.xcframework in Frameworks`
- `PBXFileReference` to `vendor/ZoomMeetingSDK/lib/zoomcml.xcframework`

This closes the question whether the current generated project has an XcodeGen reference. **It does**. It does **not** demonstrate that a fresh app build packaged the framework into `.app/Frameworks` or that the simulator loads successfully. Next operator: Xcode → Product → Clean Build Folder, run iPad (A16) simulator. If `dyld` still reports missing `zoomcml.framework`, list the vendor xcframework subframeworks and exact built app's Frameworks directory to diagnose embed phase/file output. No additional project changes justified from grep alone.

## 2026-11-15 — Confirmed SDK package includes zoomcml but existing app bundle does not
Operator `find` shows `zoomcml.framework` present in both `ios-arm64-simulator` and `ios-arm64` vendor XCFramework slices. Current inspected `.app/Frameworks` contains `MobileRTC.framework` only (one additional empty bundle also found). The inspected product directories have **00:40–00:52** timestamps; latest operator Terminal session began around 09:04, so **may be stale outputs**. Project spec and generated `.pbxproj` have correct zoomcml embed entries, but a freshly generated app bundle has not been verified.

Instead of changing more project settings, force an isolated clean Simulator build with a **new** DerivedData location:

```bash
cd ~/doctutorials-zoom-suite/ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
xcodebuild -project DocTutorialsScreenShare.xcodeproj -scheme DocTutorialsScreenShare -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath "$HOME/Downloads/DocTutorialsIpadBuildCheck" CODE_SIGNING_ALLOWED=NO clean build > "$HOME/Downloads/DocTutorialsIpadBuildCheck.log" 2>&1
echo "Build exit status: $?"
tail -n 12 "$HOME/Downloads/DocTutorialsIpadBuildCheck.log"
ls -la "$HOME/Downloads/DocTutorialsIpadBuildCheck/Build/Products/Debug-iphonesimulator/DocTutorialsScreenShare.app/Frameworks"
```

This is a throwaway **unsigned Simulator packaging diagnosis**; a succeeding build does not prove Apple signing or Zoom auth. If zoomcml appears in the new bundle, Xcode's prior DerivedData was stale; return to fresh Xcode build/test. If it is still absent, inspect complete clean build output for `zoomcml` copy phase and exact generated `PBXCopyFilesBuildPhase` / target phase ordering; do not guess. Source: https://developer.apple.com/documentation/xcode/addressing-missing-framework-crashes .


## 2026-11-15 — Arm64-only Zoom SDK: x86_64 Simulator linker failure fixed in spec, retest pending
The first *fresh isolated* `xcodebuild` produced **exit code 65**, with:
- `MobileRTC.xcframework` and `zoomcml.xcframework`: missing architecture `x86_64`
- failing `Ld .../Objects-normal/x86_64/.../DocTutorialsScreenShare.debug.dylib`
- resulting empty fresh `.app/Frameworks` (build aborted before the embed phase)

Root cause of this **build attempt** is verified: official Zoom docs say Meeting SDK **6.7.5 and later omit x86 iOS Simulator**, whereas our extracted 7.2.5 package includes **ARM64 simulator and ARM64 iPad** slices. Using a generic Simulator destination led Xcode to try compiling x86_64 as well. This is **not evidence** that the old missing-zoomcml runtime issue is resolved or still occurs after a successful clean build.

A minimal fix is now committed to the SDK-specific `project-sdk.yml`:

```yaml
settings:
  base:
    "EXCLUDED_ARCHS[sdk=iphonesimulator*]": x86_64
```

This SDK-app-only setting excludes Intel simulator, not ARM64 simulator nor physical iPad. The prior `MobileRTC` + `zoomcml` Embed & Sign settings remain. UI-only project stays unchanged.

**Rerun on Mac, keeping the diagnostic directory separate from Xcode's standard DerivedData:**

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
xcodebuild -project DocTutorialsScreenShare.xcodeproj -scheme DocTutorialsScreenShare -configuration Debug -destination 'generic/platform=iOS Simulator' -derivedDataPath "$HOME/Downloads/DocTutorialsIpadBuildCheck" CODE_SIGNING_ALLOWED=NO clean build > "$HOME/Downloads/DocTutorialsIpadBuildCheck.log" 2>&1
echo "Build exit status: $?"
tail -n 18 "$HOME/Downloads/DocTutorialsIpadBuildCheck.log"
ls -la "$HOME/Downloads/DocTutorialsIpadBuildCheck/Build/Products/Debug-iphonesimulator/DocTutorialsScreenShare.app/Frameworks"
```

Expected fresh build architecture is `arm64` only. Expected embedded frameworks after link: `MobileRTC.framework` and `zoomcml.framework`. If exit status remains 65, collect `grep -n 'error:' ~/Downloads/DocTutorialsIpadBuildCheck.log | head -n 15` and the `xcodebuild` architecture lines. If build passes but `zoomcml.framework` is absent, investigate XcodeGen copy phase packaging separately; do not conflate issues or claim SDK runtime success.

Sources: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/ ; https://developer.apple.com/documentation/technotes/tn3117-resolving-build-errors-for-apple-silicon .


## 2026-11-15 — SDK Stage 4B ARM64 Simulator build and embed verification PASS
Operator isolated clean `xcodebuild` after XcodeGen ARM64-only Simulator fix now outputs **`BUILD SUCCEEDED`**. Fresh app bundle framework listing from 09:16 shows:
- `MobileRTC.framework` present
- `zoomcml.framework` present

Therefore **fresh ARM64 Simulator compile and dynamic framework packaging have passed**; prior missing zoomcml from older products and unsupported x86_64 generic-link failures are resolved at the build/package stage. This is an **unsigned diagnostic build**, so real app launch/test remains independently unverified.

**Next operator checkpoint:** Open `DocTutorialsScreenShare.xcodeproj`, select iPad (A16) Simulator, Product → Clean Build Folder (Shift+Cmd+K), Cmd+R to launch then Cmd+U to rerun five policy XCTest cases with SDK source linked. The Join button and screen sharing remain disabled; no real Meeting SDK authentication, Zoom participant join, faculty HTTPS assignment API or ReplayKit broadcast has been completed. Report any remaining loader errors from a fresh app run, without sharing Zoom credentials.


## 2026-11-15 — Zoom SDK-linked app visibly launches in Simulator: PASS
Operator screenshot at **09:19 AM, 15 Nov 2026** displays DocTutorials faculty iPad SwiftUI app after the successful fresh ARM64 build including `MobileRTC.framework` and `zoomcml.framework`. UI is responsive enough to render full layout. The earlier missing `zoomcml` loader crash is no longer blocking this launch.

The app still clearly states **Development preview — no meeting is joined or broadcast** and the Zoom Meeting participant Join button is disabled. **This is a startup + UI pass only**, not an SDK authorization or Zoom meeting join success; the SDK adapter code remains unconnected to faculty assignment/login. ReplayKit extension not yet built.

**Next check:** run Cmd+U from Xcode with iPad (A16) Simulator selected; report green 5/5 `ScreenSharePolicyTests`. If tests pass, proceed to HTTPS faculty authentication/assignment and backend-issued Meeting SDK JWT join ticket in the separate Basic sandbox, not production.


## 2026-11-15 — Stage 4B Xcode SDK-enabled five policy tests: PASS
Operator Mac Terminal verifies:
- **`Test exit status: 0`**
- **`Executed 5 tests, with 0 failures (0 unexpected)`**
- **`** TEST SUCCEEDED **`**
- Xcode test destination: `platform=iOS Simulator,name=iPad (A16),OS=27.2`. This is a **new successful test run with SDK-linked project**, distinct from earlier five UI-only shell policy tests.
- Previous clean isolated ARM64 build / both required runtime frameworks / visually confirmed simulator launch already passed.
- Existing nonfatal `Info.plist` interface orientation warning should be resolved before release. Do not confuse it with a test or SDK failure.

**Next active milestone:** real, security-gated Meetings-only sandbox participant join. Implement a proper HTTPS DocTutorials faculty authentication + assignment authorization endpoint `POST /api/sessions/{id}/join/ipad`. Reuse backend-only Meeting SDK JWT signer and strictly scoped participant ticket; **never embed Zoom SDK Client Secret or production host credentials** in Swift code, logs or Git. The local Basic sandbox read-only FastAPI operator API is loopback-only and is NOT the faculty HTTPS join backend. Then wire SwiftUI Join button only after an actual faculty session and assigned meeting ticket, and drive UI meeting status from real `MobileRTCMeetingServiceDelegate` callbacks; keep broadcast gate disabled until share permission and ReplayKit implementation are proven on a real iPad. Backend JWT offline tests: `python3 -m unittest discover -s tests -p 'test_ipad_sdk_jwt.py' -v` (assistant previously reported 8/8 PASS locally; operator Mac run still not reported).


## 2026-11-15 — JWT signer Mac 8/8 PASS; next server-side faculty authorization scaffold staged
The operator's Mac Terminal explicitly reports **`Ran 8 tests in 0.000s / OK`** for `tests/test_ipad_sdk_jwt.py`. This passes the **backend HS256 Meeting SDK participant JWT signer unit tests**, not real credential authorization or a Zoom meeting connection.

**New Stage 4B authorization code committed**:
- `backend/ipad_join_authorization.py`: domain-only `SandboxIPadJoinService`, `AuthenticatedFaculty`, `AssignedSandboxMeeting`, `AuthorizedIPadJoinTicket`. It requires an authenticated faculty principal from *trusted server auth*, checks faculty-to-session assignment, Basic sandbox-only environment, session eligibility, numeric Zoom Meeting ID and join window (15 min before until 15 min after scheduled end), and issues a 30-minute JWT **as participant role=0** via backend-only secret. Ticket contains `meetingNumber`, `meetingPasscode`, `displayName`, `meetingSDKJWT`, `expiresAtEpoch`; it must only be sent over authenticated HTTPS and never logged.
- `tests/test_ipad_join_authorization.py`: 12 offline authorization and invalid-input tests, **operator execution PENDING**. No real Zoom IDs or credentials in tests.
- This is intentionally **NOT a public FastAPI route**, not a faculty login system, not a meeting assignment database and not wired to the SwiftUI app. In particular, **never expose `backend/meetings_api.py` localhost operator service publicly**, and never accept faculty identity or assigned meeting metadata directly from app JSON. Do not turn on the Join button until authenticated HTTPS endpoint and signed join ticket are integrated and runtime verified.

**Mac test command:**

```bash
cd ~/doctutorials-zoom-suite
git pull
python3 -m unittest discover -s tests -p 'test_ipad_join_authorization.py' -v
```

Expected after testing: `Ran 12 tests` and `OK`. This number is **not yet confirmed**. Next milestone after proof is connecting genuine DocTutorials faculty authentication / server-owned sandbox assignment persistence to the endpoint, then requesting join ticket from the SwiftUI app and invoking the compiled Zoom SDK adapter only when authorized. Actual Zoom connection, share permission and ReplayKit broadcast still remain unverified.

Official source: https://developers.zoom.us/docs/meeting-sdk/auth/


## 2026-11-15 — 12/12 sandbox faculty join authorization tests PASS on operator Mac
- User's Terminal output confirms **`Ran 12 tests in 0.001s`, `OK`** for `test_ipad_join_authorization.py`.
- With previous Mac backend JWT **8/8 PASS** and iPad SDK-enabled policy XCTest **5/5 PASS**, the current backend domain logic for scoped non-host join tickets has passed offline validation.
- **Not yet implemented or verified:** actual DocTutorials faculty sign-in, server-controlled assignment database, secret vault/provisioning, HTTPS `POST /api/sessions/{id}/join/ipad`, iPad authenticated request, Zoom SDK JWT authentication, observed participant join, real-device ReplayKit broadcast.
- Next implementation work should focus on the authenticated HTTPS faculty ticket boundary, followed by first Basic sandbox meeting join. Do not expose the existing loopback-only operator API publicly or enable Join from a sample class.


## 2026-11-15 — HTTPS iPad join-ticket API + client scaffold committed; validation pending
**Code staged:** `backend/ipad_join_http.py` is an explicit-activation-only FastAPI factory for `POST /api/sessions/{internal_id}/join/ipad`, wrapping existing server-only Basic sandbox `SandboxIPadJoinService`. Enforces trusted hosts, HTTPS ASGI scope, Bearer faculty verifier callback, no user-supplied assignment/Zoom metadata body, and no-store ticket responses. Generic 401 on invalid identity, 403 for unauthorized meeting, 426 for non-HTTPS, 503 when disabled. No CORS, interactive API docs or auto-run server. **No real faculty token verifier has yet been configured**, so this is not a live usable endpoint or secure deployment.

**19 new tests committed:** `tests/test_ipad_join_http.py` (TestClient with fake faculty verifier and fake Basic sandbox assignment; no Zoom call). `backend/requirements-ipad-dev.txt` adds httpx for testing. **19/19 NOT YET CLAIMED**; operator Mac execution pending.

**iPad HTTPS ticket transport staged:** `SDKApp/HTTPSFacultyJoinTicketClient.swift` uses HTTPS-only API origin, ephemeral URLSession with redirects rejected, in-memory faculty token, post-only call and bounded response/expiry validation. No login/token is fabricated, no UI call is wired, no join enabled, no ReplayKit controls unlocked. **Not yet compiled under Xcode after new source was added**. The SDK-linked project's existing 5/5 test pass predates this newly added file.

Runbook: **[21-IPAD-JOIN-API-RUNBOOK.md](21-IPAD-JOIN-API-RUNBOOK.md)**. **Next operator test** after `git pull`: create a Python venv under `~/.venvs/doctutorials-ipad-api`, install `backend/requirements-ipad-dev.txt`, execute `python -m unittest discover -s tests -p 'test_ipad_join_http.py' -v` from repository root. Expect `Ran 19 tests` / `OK`; do not claim until seen. Then regenerate `project-sdk.yml` and run Xcode Cmd+B/Cmd+U for Swift compile/regression check. Any real Zoom SDK join must wait for provider-backed faculty auth, server-owned assignments, secure HTTPS deployment, and backend secret provisioning.


## 2026-11-15 — 19/19 HTTPS join-ticket HTTP tests PASS on operator Mac
Operator terminal reports **`Ran 19 tests in 0.085s`, `OK`** for `tests/test_ipad_join_http.py`. This confirms the offline FastAPI TestClient contract tests pass, including auth/permission denials, HTTPS and host restrictions, disabled-by-default behavior, response shape, no-store and no demo endpoints. No live identity system or public server exists yet.

**Next acceptance check:** compile the newly committed `SDKApp/HTTPSFacultyJoinTicketClient.swift` in the SDK-linked iPad project and rerun five XCTest policy tests:

```bash
cd ~/doctutorials-zoom-suite
git pull
cd ipad/DocTutorialsScreenShare
xcodegen generate --spec project-sdk.yml
open DocTutorialsScreenShare.xcodeproj
```

Choose **DocTutorialsScreenShare** and **iPad (A16) Simulator**; press **Cmd+B**, then **Cmd+U**. The Swift client is still unconnected to Join; a compilation pass does not imply any actual Zoom SDK authorization/join. If compilation fails, capture first red Xcode error. The HTTP tests use fake faculty verification and sandbox meeting records; production security controls and backend HTTPS deployment remain pending.
