import XCTest
@testable import DocTutorialsScreenShare

final class ScreenSharePolicyTests: XCTestCase {
    func testDisconnectedNeverOffersBroadcast() {
        XCTAssertFalse(ScreenSharePolicy.mayOfferBroadcast(
            connection: .disconnected,
            privacyAcknowledged: true,
            zoomSharePermissionConfirmed: true
        ))
    }

    func testConnectedButNoPrivacyConsentNeverOffersBroadcast() {
        XCTAssertFalse(ScreenSharePolicy.mayOfferBroadcast(
            connection: .inMeeting,
            privacyAcknowledged: false,
            zoomSharePermissionConfirmed: true
        ))
    }

    func testConnectedButNoZoomPermissionNeverOffersBroadcast() {
        XCTAssertFalse(ScreenSharePolicy.mayOfferBroadcast(
            connection: .inMeeting,
            privacyAcknowledged: true,
            zoomSharePermissionConfirmed: false
        ))
    }

    func testBroadcastOnlyAfterAllThreeGates() {
        XCTAssertTrue(ScreenSharePolicy.mayOfferBroadcast(
            connection: .inMeeting,
            privacyAcknowledged: true,
            zoomSharePermissionConfirmed: true
        ))
    }

    func testStatusNeverClaimsConnectedWhenDisconnected() {
        XCTAssertEqual(ScreenSharePolicy.statusText(for: .disconnected), "Not connected to a Zoom meeting")
    }
}
