# Official References and Verification Log

Verified/consulted 2026-11-13. Zoom documentation and SDK capabilities may change; reverify before implementation or deployment.

## Zoom support
- Automatic recording for meetings/webinars: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0067954
- Cloud recording management: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0065362
- Cloud recording settings: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0064676
- Troubleshooting cloud automatic recording: https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0058972

## Zoom Developer
- Windows Plugin SDK getting started: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/
- Windows Plugin SDK integration: https://developers.zoom.us/docs/plugin-sdk/windows/integrate/
- Windows Plugin SDK authentication: https://developers.zoom.us/docs/plugin-sdk/windows/start-join-mtg-webinar/authentication/
- Meeting SDK for iOS: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/
- Meeting SDK join: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- iOS ReplayKit sharing: https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/screen-share/
- Zoom meeting/webinar webhook events: https://developers.zoom.us/docs/api/meetings/events/
- General Meeting SDK policy: https://developers.zoom.us/docs/meeting-sdk/

## Milestone 2 — Verified against current Zoom developer docs (2026-11-13)
- Create S2S OAuth app (current console steps / activation): https://developers.zoom.us/docs/internal-apps/create/
- S2S role permissions and account-wide scope: https://developers.zoom.us/docs/internal-apps/
- S2S token and no refresh token: https://developers.zoom.us/docs/internal-apps/s2s-oauth/
- Granular admin scopes for users, meetings, webinars and cloud recordings: https://developers.zoom.us/docs/internal-apps/oauth-scopes-granular/
- Meeting API and cloud recording endpoints: https://developers.zoom.us/docs/api/meetings/
- Webhooks HTTPS/CRC/HMAC/event subscriptions: https://developers.zoom.us/docs/api/webhooks/
- Meeting/webinar started/ended events: https://developers.zoom.us/docs/api/meetings/events/

These confirm documentation, **not** that the customer app has been configured or tested.

## Milestone 2 — API smoke test implementation (2026-11-13)
- S2S `account_credentials` POST grant: https://developers.zoom.us/docs/integrations/oauth/
- S2S expiry and no refresh token: https://developers.zoom.us/docs/internal-apps/s2s-oauth/
- List active users `GET /users`: https://developers.zoom.us/docs/api/users/
- List user meetings/webinars and get details: https://developers.zoom.us/docs/api/meetings/
- Read-only scope reference: https://developers.zoom.us/docs/internal-apps/oauth-scopes-granular/

Python standalone proof and nine offline unit tests were run; **no actual tenant API test was performed**.

## Verification matrix to complete
| Capability | Evidence needed | Status |
|---|---|---|
| Cloud recording account default and exceptions | Test on each host; existing webinars | Documented, not configured |
| Webinar practice session cloud backup | Confirm only in live phase | Documented, not tested |
| Four simultaneous Zoom users on one Windows host | 4-worker load test | Unverified |
| Local recording control via Windows Plugin SDK | API sample + live test | Unverified |
| Host startup via worker with no shared faculty password | Live host test | Unverified |
| SDK iPad panelist screen sharing | Real iPad + webinar test | Unverified |
| Apple ReplayKit whole-device sharing | Real iPad test | Documented, not implemented |
| Backend cloud recording download scopes/webhook | OAuth + signed webhook test | Documented, not implemented |

## Gate 3A — Windows Plugin SDK developer evidence (consulted 2026-11-14)
- Windows plugin SDK minimum Zoom Workplace client **7.0.2**, SDK download path and Visual Studio prerequisite: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/
- Official `PSDKTest.exe` demo, Release x64 build, IPC connection and recording capability/start test panels: https://developers.zoom.us/docs/plugin-sdk/windows/get-started/try-demo-app/
- General App Plugin SDK library integration and `plugin_sdk:read:connection_meta` scope: https://developers.zoom.us/docs/plugin-sdk/windows/integrate/
- IPC OAuth auth context and asynchronous auth result callback: https://developers.zoom.us/docs/plugin-sdk/windows/start-join-mtg-webinar/authentication/
- Plugin SDK Windows API reference (SDK-specific interfaces MUST be inspected; Meeting SDK recording methods are not proof of Plugin SDK parity): https://marketplacefront.zoom.us/sdk/plugin/windows/index.html
- Permission/version mismatch/not-implemented error codes: https://developers.zoom.us/docs/plugin-sdk/windows/error-codes/

**Verified from documentation:** An official Plugin SDK Windows demo includes local recording capability checks and start actions. **Not yet verified in customer's environment:** actual SDK IPC auth, local start/stop, pause/resume support, permissions, MP4 finalization, Windows VM scaling. **No Plugin SDK binary has been downloaded, compiled or executed by the assistant.**

## Active Stage 4A iPad Meeting SDK full-device sharing — consulted 2026-11-14
- Zoom Meeting SDK iOS getting started and compatibility: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/
- Meeting SDK iOS 7.0.0+ Xcode 26+ integration prerequisites: https://developers.zoom.us/docs/meeting-sdk/ios/integrate/
- Full-device ReplayKit, App Groups, dedicated Broadcast Upload Extension and MobileRTCScreenShare forwarding/callbacks: https://developers.zoom.us/docs/meeting-sdk/ios/default-ui/basic-features/screen-share/
- Mute iPad mic/camera when joining, plus real meeting state callbacks: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- Server-issued JWT and external account review/ZAK/OBF rules: https://developers.zoom.us/docs/meeting-sdk/auth/
- Apple RPSystemBroadcastPickerView (deprecated, still documented in Zoom iOS share guide): https://developer.apple.com/documentation/replaykit/rpsystembroadcastpickerview

**Documentation confirms API architecture, not an installed or tested app.** iPad Stage 4A UI-only source scaffold, XcodeGen spec, five XCTest cases and staged uncompiled ReplayKit SampleHandler template were committed 2026-11-14. No Mac Xcode build, Zoom SDK join, extension signing or iPad transmission test completed. External-paid-account app review and token requirements must be validated before cross-account joining. Meetings only; webinar and Windows recorder deferred.

## Stage 4B — Zoom iOS SDK initialization, join callbacks and signing (rechecked 2026-11-15)
- Official iOS integration sample shows `MobileRTCSDKInitContext`, `MobileRTCAuthService.jwtToken`, `sdkAuth()`, and `onMobileRTCAuthReturn`: https://developers.zoom.us/docs/meeting-sdk/ios/build-an-app/implement-features/
- Official non-host join has `MobileRTCMeetingJoinParam`, `noAudio`, `noVideo`, `MobileRTCMeetingService.joinMeeting(with:)`; connection status determined from `onMeetingStateChange` and `onMeetingError`: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- Official signing claims for native Meeting SDK (`appKey`, `iat`, `exp`, `tokenExp`) and HS256 backend recommendation; `mn` and `role` optional for native: https://developers.zoom.us/docs/meeting-sdk/auth/
- iOS Meeting SDK `MobileRTCMeetingState_InMeeting` and waiting-room/connecting/failed states: https://marketplacefront.zoom.us/sdk/meeting/ios/_mobile_r_t_c_constants_8h.html
- XcodeGen additive `include` merge for additional SDK-only source directory: https://yonaskolb.github.io/XcodeGen/Docs/ProjectSpec.html

The code for SDK init/participation and signer is STAGED. Documentation is not a live Zoom Meeting SDK join test, secure faculty endpoint, physical-device test or functioning broadcast.

## Stage 4B — SDK 7.2.5 `zoomcml` runtime dependency, verified 2026-11-15
- Zoom's iOS integration page lists `MobileRTC.xcframework`, `MobileRTCResources.bundle`, `MobileRTCScreenShare.xcframework`, and `zoomcml.xcframework`; the last is described as an optional feature framework in general: https://developers.zoom.us/docs/meeting-sdk/ios/integrate/
- On October 15, 2026, Zoom staff stated `zoomcml` has been **mandatory for physical iPhones since SDK 6.4.5**, and promised documentation updates. Operator's SDK 7.2.5 launch on iPadOS 27.2 simulator empirically fails with `@rpath/zoomcml.framework/zoomcml` absent; thus it is a **required runtime dependency** for our current build too: https://devforum.zoom.us/t/is-the-ios-meeting-sdk-still-actively-supported/147169
- Apple's dynamic linker missing-framework guidance (embed a linked runtime dependency in app bundle): https://developer.apple.com/documentation/xcode/addressing-missing-framework-crashes
- Corrected XcodeGen `project-sdk.yml` to embed and sign `zoomcml` plus `MobileRTC`; simulator retest is pending.


## Stage 4B — Simulator architecture compatibility, verified 2026-11-15
- Zoom **Meeting SDK 6.7.5+ does not support x86 iOS Simulator**. The user's SDK 7.2.5.40220 has `ios-arm64-simulator` and `ios-arm64`, not `ios-x86_64-simulator`. Official: https://developers.zoom.us/docs/meeting-sdk/ios/get-started/
- Apple architecture guidance: prefer default `ARCHS`, selectively use `EXCLUDED_ARCHS` on impacted targets for missing architectures, avoid global architecture hacks: https://developer.apple.com/documentation/technotes/tn3117-resolving-build-errors-for-apple-silicon
- Stage 4B project SDK-only spec now excludes `x86_64` for Simulator; next operator isolated build is unverified. Do not confuse simulator architecture build failure with dynamic-loader missing `zoomcml`.


## Stage 4B — Meetings-only authorization rules (rechecked 2026-11-15)
- JWT from the Meeting SDK app is sufficient for **non-host attendee join within the owning developer Zoom account**, but not for other accounts; external meetings need Zoom review and applicable ZAK/OBF authorization. Generate SDK JWT on a trusted backend; native appKey / iat / exp / tokenExp required, mn / role=0 supported: https://developers.zoom.us/docs/meeting-sdk/auth/
- iOS meeting join response is a request; authoritative joining status comes from MobileRTCMeetingServiceDelegate callbacks: https://developers.zoom.us/docs/meeting-sdk/ios/start-join-mtg-webinar/join-meeting/
- The DocTutorials faculty session assignment, authentication and ephemeral ticket HTTP API are **our own application policies**, not offered by Zoom's SDK as a built-in faculty identity provider.


## Stage 4B — HTTPS authenticated faculty iPad join-ticket boundary (consulted 2026-11-15)
- Zoom Meeting SDK JWTs are server-signed using the separate Meeting SDK app Client ID and Client Secret. A **non-host participant in a meeting in the same developer Zoom account** can use the signed JWT; production external-account joins need separate Zoom review and applicable ZAK/OBF. Required native claims appKey/iat/exp/tokenExp and optional mn/role=0: https://developers.zoom.us/docs/meeting-sdk/auth/
- FastAPI HTTPS deployment concerns: https://fastapi.tiangolo.com/deployment/https/
- Starlette HTTPS/TrustedHost middleware: https://www.starlette.io/middleware/
- Apple's network App Transport Security HTTPS policy: https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity
- No claim that library examples substitute for real DocTutorials faculty auth, deployment protections or live Zoom testing. The HTTPS join API scaffold is committed but OFF by default.


## 2026-11-15 — First-party password handling (Basic sandbox pilot)
- OWASP Password Storage Cheat Sheet: salted slow password KDF, scrypt N=2^17, r=8, p=1 fallback when Argon2id unavailable: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- OWASP Authentication Cheat Sheet: generic error messages, login throttling and avoiding username enumeration: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- DocTutorials' static faculty password is a separate first-party security principal; it is neither a Zoom Meeting password nor an SDK signing credential. Basic sandbox login routes remain OFF until security gates and operator testing pass.
