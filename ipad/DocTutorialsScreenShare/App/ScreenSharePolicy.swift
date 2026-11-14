import Foundation

/// These are observed connection states, not desired states.
/// Stage 4A has no SDK connection implementation, so the real state remains disconnected.
enum MeetingConnectionState: Equatable {
    case disconnected
    case connecting
    case inMeeting
    case failed
}

enum ScreenSharePolicy {
    static func mayOfferBroadcast(
        connection: MeetingConnectionState,
        privacyAcknowledged: Bool,
        zoomSharePermissionConfirmed: Bool
    ) -> Bool {
        connection == .inMeeting && privacyAcknowledged && zoomSharePermissionConfirmed
    }

    static func statusText(for connection: MeetingConnectionState) -> String {
        switch connection {
        case .disconnected: return "Not connected to a Zoom meeting"
        case .connecting: return "Connecting to Zoom"
        case .inMeeting: return "Connected to Zoom meeting"
        case .failed: return "Meeting connection failed"
        }
    }
}
