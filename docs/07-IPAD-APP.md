# Faculty iPad App — v0.2 (ACTIVE — Meetings-first)

**2026-11-14 operator priority:** Develop the DocTutorials iPad screen-sharing app now; Windows central recorder last. Initial proof is an authorized **Zoom Meeting in the separate Basic sandbox**. Webinar panelist experience below remains **future**, not part of the active test. See [Stage 4A runbook](20-IPAD-MEETINGS-SCREENSHARE-DEVELOPMENT.md).

**Committed implementation:** `../ipad/DocTutorialsScreenShare/` includes an iPad SwiftUI UI shell, privacy and actual-SDK-state gating, five unrun XCTest policy tests, XcodeGen project spec and an **uncompiled** Zoom ReplayKit SampleHandler template. This is not a working screen-share app yet; no Xcode build, SDK joining or device broadcast was performed.

## Objective
One installable branded DocTutorials app for all faculty with DocTutorials login, assigned class list, verified Zoom webinar panelist joining, and iPad full-screen broadcasting.

## Proposed UI
- Login / session refresh
- Today's classes with course, subject, topic, start time, status
- Join **Meeting first** and 'present from iPad' mode (mic/camera off by default); webinar later
- Start Screen Broadcast using Apple's ReplayKit picker (user must confirm)
- Show server-side **cloud backup / local recording** status, independently labeled
- Recover from disconnect and present instructions for ending screen share

## Technical approach
- Swift + SwiftUI, Zoom Meeting SDK for iOS, ReplayKit Broadcast Upload Extension, `MobileRTCScreenShare.framework` in extension only.
- Backend signs SDK authentication requests. Do not store secret in iPad binary.
- Zoom Meeting SDK supports sharing full screen through ReplayKit; app must obtain the required user-initiated broadcast confirmation.
- An Apple Pencil note-taking app can be opened while screen broadcast continues; confirm actual webinar screen-share entitlement.
- Separate licensed Zoom host credentials are never distributed to faculty.
- Research iPad App Store unlisted / TestFlight distribution and review requirements before release.

## Must-pass prototype (original full-product wishlist; Gate 4A Meetings-only proof comes first)
1. Faculty logs in using DocTutorials credentials.
2. Session appears only when assigned.
3. Join existing account-hosted webinar as panelist without host password.
4. Camera and audio remain off by default for iPad.
5. Tap to start ReplayKit screen broadcast; open Goodnotes/Notability, draw with Apple Pencil.
6. Laptop camera/audio + iPad share reach audience and Windows recorder together.
7. iPad reconnects after temporary network interruption with explicit screen-share restart.
8. No accidental broadcast of sensitive notifications; show privacy warning before full-device sharing.

## Unresolved
- Exact panelist token/invitation mechanism for Meeting SDK iOS in our webinar configuration.
- Same developer account ownership vs multiple Zoom host users.
- SDK/Apple device version matrix and iOS App Store requirements at implementation time.

References: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/ and https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/screen-share/
