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
