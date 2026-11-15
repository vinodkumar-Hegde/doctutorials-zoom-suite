import Foundation
import MobileRTC
import SwiftUI

/// An ephemeral, authorization-scoped response from the DocTutorials backend.
/// Do not create this from an untrusted text field or a shared Zoom join link.
/// The backend must authenticate faculty and verify the assigned sandbox session.
struct AuthorizedMeetingJoinTicket {
    let meetingNumber: String
    let meetingPasscode: String
    let displayName: String
    let meetingSDKJWT: String

    var isPlausible: Bool {
        (9...13).contains(meetingNumber.count)
            && meetingNumber.utf8.allSatisfy { $0 >= 48 && $0 <= 57 }
            && !displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && meetingSDKJWT.split(separator: ".").count == 3
    }
}

/// Zoom Meeting SDK adapter: OBSERVED callbacks, not optimistic join states.
/// Included ONLY by project-sdk.yml (never by the known-good UI-only spec).
///
/// Stage 4B milestone: compile the adapter against the downloaded vendor SDK.
/// It is deliberately not called from the UI until we have a verified HTTPS
/// faculty login + assigned-session backend. No host passwords or SDK secrets.
final class ZoomMeetingJoinAdapter: NSObject, ObservableObject, MobileRTCAuthDelegate, MobileRTCMeetingServiceDelegate {
    @Published private(set) var connection: MeetingConnectionState = .disconnected
    @Published private(set) var statusMessage = "No authorized meeting assigned"

    /// MUST NOT become true merely because the Meeting SDK is authenticated
    /// or a meeting-state callback reports inMeeting. The later ReplayKit
    /// integration must separately observe sharing permission and extension.
    @Published private(set) var zoomSharePermissionConfirmed = false

    private var pendingTicket: AuthorizedMeetingJoinTicket?

    /// Only call on main thread AFTER faculty assignment has been verified
    /// by the backend, which must issue a short-lived SDK JWT.
    func joinAssignedMeeting(_ ticket: AuthorizedMeetingJoinTicket) {
        assert(Thread.isMainThread)
        guard connection == .disconnected || connection == .failed else { return }
        guard ticket.isPlausible else {
            fail("Assigned meeting credentials are invalid.")
            return
        }

        connection = .connecting
        statusMessage = "Authorizing Zoom Meeting SDK"
        zoomSharePermissionConfirmed = false
        pendingTicket = ticket

        // Zoom requires MobileRTCResources.bundle in the app's Copy Bundle
        // Resources phase. Supply the actual path rather than relying on
        // SDK default discovery (which differs across framework packages).
        guard let resourcesPath = Bundle.main.path(
            forResource: "MobileRTCResources", ofType: "bundle"
        ) else {
            fail("Zoom SDK resources are missing from the app bundle.")
            return
        }

        let context = MobileRTCSDKInitContext()
        context.domain = "zoom.us"
        context.enableLog = false // Never log Meeting SDK JWTs, passcodes or secrets.
        context.bundleResPath = resourcesPath
        guard MobileRTC.shared().initialize(context) else {
            fail("Zoom SDK core could not initialize. Check supported iPadOS and bundled frameworks.")
            return
        }
        guard let auth = MobileRTC.shared().getAuthService() else {
            fail("Zoom SDK initialized but authentication service is unavailable.")
            return
        }

        auth.delegate = self
        auth.jwtToken = ticket.meetingSDKJWT
        auth.sdkAuth()
    }

    func onMobileRTCAuthReturn(_ returnValue: MobileRTCAuthError) {
        DispatchQueue.main.async { [weak self] in
            self?.handleAuthorization(returnValue)
        }
    }

    private func handleAuthorization(_ result: MobileRTCAuthError) {
        guard connection == .connecting else { return }
        guard result == .success, let ticket = pendingTicket else {
            fail("Zoom Meeting SDK authorization was rejected.")
            return
        }
        // No app-side credentials survive beyond the authorization window.
        pendingTicket = nil
        guard let meetingService = MobileRTC.shared().getMeetingService() else {
            fail("Zoom meeting service is unavailable.")
            return
        }
        meetingService.delegate = self

        if let settings = MobileRTC.shared().getMeetingSettings() {
            settings.setAutoConnectInternetAudio(true)
            settings.setMuteAudioWhenJoinMeeting(true)
            settings.setMuteVideoWhenJoinMeeting(true)
        }

        let join = MobileRTCMeetingJoinParam()
        join.userName = ticket.displayName
        join.meetingNumber = ticket.meetingNumber
        join.password = ticket.meetingPasscode
        join.noAudio = true
        join.noVideo = true

        statusMessage = "Joining assigned Zoom meeting"
        let result = meetingService.joinMeeting(with: join)
        // An immediate SDK success only means the join request was accepted.
        // Wait for the onMeetingStateChange(.inMeeting) callback.
        if result != .success {
            fail("Zoom rejected the meeting join request.")
        }
    }

    func onMeetingStateChange(_ state: MobileRTCMeetingState) {
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            self.zoomSharePermissionConfirmed = false
            switch state {
            case .inMeeting:
                self.connection = .inMeeting
                self.statusMessage = "Connected to assigned Zoom meeting"
            case .idle, .ended:
                self.connection = .disconnected
                self.statusMessage = "Not connected to a Zoom meeting"
            case .failed:
                self.fail("Zoom meeting connection failed.")
            default:
                // Waiting room, waiting for host and reconnecting are NOT
                // valid proof of a joined meeting or screen-sharing rights.
                self.connection = .connecting
                self.statusMessage = "Waiting for a Zoom meeting connection"
            }
        }
    }

    func onMeetingError(_ error: MobileRTCMeetError, message: String?) {
        DispatchQueue.main.async { [weak self] in
            // Do not show/log Zoom's raw error message: it may contain IDs.
            self?.fail("Zoom reported a meeting connection error.")
        }
    }

    private func fail(_ message: String) {
        assert(Thread.isMainThread)
        pendingTicket = nil
        connection = .failed
        zoomSharePermissionConfirmed = false
        statusMessage = message
    }
}
