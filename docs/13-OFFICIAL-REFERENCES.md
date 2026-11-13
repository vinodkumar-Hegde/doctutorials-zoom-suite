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
