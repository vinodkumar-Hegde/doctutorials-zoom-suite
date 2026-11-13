# Faculty iPad App — v0.1

## Objective
One installable branded DocTutorials app for all faculty with DocTutorials login, assigned class list, verified Zoom webinar panelist joining, and iPad full-screen broadcasting.

## Proposed UI
- Login / session refresh
- Today's classes with course, subject, topic, start time, status
- Join webinar and 'present from iPad' mode (mic/camera off by default)
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

## Must-pass prototype
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
