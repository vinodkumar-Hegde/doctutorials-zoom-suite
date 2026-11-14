import ReplayKit

// STAGED ZOOM MEETING SDK INTEGRATION TEMPLATE — not part of XcodeGen build yet.
//
// Add this file ONLY to an iOS "Broadcast Upload Extension" target after:
// 1. Installing the compatible Zoom Meeting SDK iOS distribution.
// 2. Adding MobileRTCScreenShare.framework to the extension target only.
// 3. Adding the required bridging header/module import per the installed SDK.
// 4. Enabling the SAME registered App Group on the app and extension.
// 5. Passing this App Group to the main MobileRTC SDK initialization context.
//
// Vendor class names/delegate signatures below follow Zoom's official
// screen-share guide; compile and re-check them against the downloaded SDK.
// Do not put OAuth client secrets or host credentials in this extension.
//
// Requires MobileRTCScreenShareService and MobileRTCScreenShareServiceDelegate
// from the vendor framework. The screen-share service isn't included in this repo.

final class SampleHandler: RPBroadcastSampleHandler, MobileRTCScreenShareServiceDelegate {
    private var screenShareService: MobileRTCScreenShareService?

    override init() {
        super.init()
        screenShareService = MobileRTCScreenShareService()
        screenShareService?.delegate = self
    }

    override func broadcastStarted(withSetupInfo setupInfo: [String: NSObject]?) {
        guard let group = Bundle.main.object(forInfoDictionaryKey: "DTAppGroupIdentifier") as? String,
              group.hasPrefix("group."),
              group != "group.REPLACE_ME" else {
            finishBroadcastWithError(NSError(
                domain: "DocTutorialsScreenShare",
                code: 101,
                userInfo: [NSLocalizedDescriptionKey: "Broadcast App Group is not configured."]
            ))
            return
        }
        screenShareService?.appGroup = group
        screenShareService?.broadcastStarted(withSetupInfo: setupInfo)
    }

    override func broadcastPaused() {
        screenShareService?.broadcastPaused()
    }

    override func broadcastResumed() {
        screenShareService?.broadcastResumed()
    }

    override func broadcastFinished() {
        screenShareService?.broadcastFinished()
    }

    override func processSampleBuffer(
        _ sampleBuffer: CMSampleBuffer,
        with sampleBufferType: RPSampleBufferType
    ) {
        screenShareService?.processSampleBuffer(sampleBuffer, with: sampleBufferType)
    }

    func mobileRTCScreenShareServiceFinishBroadcastWithError(_ error: Error!) {
        if let error {
            finishBroadcastWithError(error)
        }
    }
}
