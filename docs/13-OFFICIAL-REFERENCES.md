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
