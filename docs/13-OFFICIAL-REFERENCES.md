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
