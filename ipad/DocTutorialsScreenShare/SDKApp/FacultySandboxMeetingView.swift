import SwiftUI

/// Actual first-party sandbox faculty login + authorized Meeting SDK join UI.
/// Built ONLY by project-sdk.yml. No mock faculty login, no fake in-meeting
/// status, and no Zoom host credentials or app secrets in the binary.
///
/// A trusted HTTPS DocTutorials backend must be deployed before login works.
/// The backend, never this iPad view, decides which session may be joined.
struct FacultySandboxMeetingView: View {
    @StateObject private var meeting = ZoomMeetingJoinAdapter()

    // Mac loopback address for the one-device Basic sandbox Simulator pilot.
    @State private var httpsOrigin = "https://localhost:8443"
    @State private var facultyID = "sandbox-faculty"
    @State private var password = ""
    // One assigned internal session in this Basic sandbox pilot. This is NOT the Zoom Meeting number.
    @State private var assignedSessionID = "ipad-sandbox-class"
    @State private var accessSession: FacultyAccessSession?

    @State private var loggingIn = false
    @State private var requestingJoin = false
    @State private var notice = "Configure your private DocTutorials HTTPS server to sign in."
    @State private var privacyAcknowledged = false

    private var isAuthenticated: Bool {
        accessSession?.isUsable == true
    }

    private var canRequestJoin: Bool {
        isAuthenticated
            && !assignedSessionID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !requestingJoin
            && (meeting.connection == .disconnected || meeting.connection == .failed)
    }

    private var canOfferBroadcast: Bool {
        ScreenSharePolicy.mayOfferBroadcast(
            connection: meeting.connection,
            privacyAcknowledged: privacyAcknowledged,
            zoomSharePermissionConfirmed: meeting.zoomSharePermissionConfirmed
        )
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    loginCard
                    meetingCard
                    shareCard
                }
                .frame(maxWidth: 760)
                .padding(24)
                .frame(maxWidth: .infinity)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Faculty Screen Share")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("DocTutorials", systemImage: "rectangle.on.rectangle")
                .font(.title2.bold())
            Text("Faculty iPad Meeting")
                .font(.largeTitle.bold())
            Text("First-party password login. Your iPad joins a Zoom Basic sandbox Meeting as a separate, muted participant; laptop handles camera and audio.")
                .foregroundStyle(.secondary)
            Label("No Meeting is connected until Zoom reports a successful join.", systemImage: "shield.lefthalf.filled")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }

    private var loginCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Faculty sign-in", systemImage: "person.crop.circle")
                    .font(.headline)

                if isAuthenticated {
                    Label("Signed in to DocTutorials (sandbox)", systemImage: "checkmark.shield")
                        .foregroundStyle(.green)
                    Text("Your sign-in expires after 15 minutes. Signing in alone does not join Zoom.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Button("Sign out") {
                        signOut()
                    }
                    .buttonStyle(.bordered)
                } else {
                    TextField("HTTPS backend URL, e.g. https://your-host.example", text: $httpsOrigin)
                        .textContentType(.URL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityIdentifier("httpsBackendOrigin")

                    TextField("Faculty ID", text: $facultyID)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textFieldStyle(.roundedBorder)
                        .accessibilityIdentifier("facultyID")

                    SecureField("Your private static password", text: $password)
                        .textContentType(.password)
                        .textFieldStyle(.roundedBorder)
                        .accessibilityIdentifier("facultyPassword")

                    Button {
                        Task { await signIn() }
                    } label: {
                        if loggingIn {
                            ProgressView()
                        } else {
                            Text("Sign in to DocTutorials")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(loggingIn || httpsOrigin.isEmpty || facultyID.isEmpty || password.isEmpty)

                    Text("The password is never stored in the app. The server URL must use trusted HTTPS; a self-signed or untrusted certificate will fail.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Label(notice, systemImage: "info.circle")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .accessibilityIdentifier("facultyLoginStatus")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var meetingCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Authorized Zoom Meeting", systemImage: "video")
                    .font(.headline)
                Label(meeting.statusMessage, systemImage: "circle.dashed")
                    .foregroundStyle(.secondary)

                TextField("Assigned class ID — not Zoom Meeting ID", text: $assignedSessionID)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .textFieldStyle(.roundedBorder)
                    .disabled(!isAuthenticated || meeting.connection == .inMeeting)
                    .accessibilityIdentifier("assignedSessionID")

                Text("A session ID is not a Zoom Meeting ID. The backend verifies that this faculty member owns the assigned sandbox class before issuing any join ticket.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                Button {
                    Task { await joinAuthorizedMeeting() }
                } label: {
                    if requestingJoin {
                        ProgressView()
                    } else {
                        Text("Join assigned meeting")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!canRequestJoin)
                .accessibilityIdentifier("joinAssignedMeeting")

                Text("Join is available only after a valid server login. Connected status is set only by the Zoom SDK's observed meeting callback.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var shareCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Share Goodnotes / iPad screen", systemImage: "rectangle.on.rectangle.angled")
                    .font(.headline)
                Toggle("I understand my entire iPad screen may be broadcast", isOn: $privacyAcknowledged)
                if canOfferBroadcast {
                    // An actual ReplayKit Broadcast Upload Extension and observed
                    // Zoom share entitlement are both REQUIRED before adding the
                    // system picker. Neither has been completed for this target.
                    Label("Waiting for ReplayKit broadcast extension integration.", systemImage: "lock.shield")
                        .foregroundStyle(.secondary)
                } else {
                    Label("Broadcast locked until Zoom connection, share permission and privacy consent are all confirmed.", systemImage: "lock.shield")
                        .foregroundStyle(.secondary)
                }
                Text("No screen media is transmitted by this version. Apple must separately confirm any future full-screen broadcast.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @MainActor
    private func signIn() async {
        guard !loggingIn else { return }
        loggingIn = true
        let enteredPassword = password
        password = "" // Never persist password in UI state after submit.
        defer { loggingIn = false }

        do {
            guard let origin = URL(string: httpsOrigin) else {
                notice = "Enter a valid HTTPS backend URL."
                return
            }
            let client = try HTTPSFacultyPasswordLoginClient(apiOrigin: origin)
            let granted = try await client.login(
                facultyID: facultyID.trimmingCharacters(in: .whitespacesAndNewlines),
                password: enteredPassword
            )
            accessSession = granted
            notice = "Signed in. Enter your assigned DocTutorials session ID to request Zoom access."
        } catch FacultyPasswordLoginError.rejectedCredentials {
            accessSession = nil
            notice = "Faculty ID or password was rejected."
        } catch FacultyPasswordLoginError.invalidConfiguration {
            notice = "A trusted HTTPS backend URL is required."
        } catch FacultyPasswordLoginError.invalidInput {
            notice = "Enter sandbox-faculty and a password between 16 and 128 characters."
        } catch FacultyPasswordLoginError.invalidServerResponse {
            accessSession = nil
            notice = "The login server returned an invalid or expired session response."
        } catch FacultyPasswordLoginError.serviceUnavailable(let status) {
            accessSession = nil
            notice = "Faculty login endpoint returned HTTP \(status)."
        } catch let error as URLError {
            accessSession = nil
            switch error.code {
            case .serverCertificateUntrusted, .secureConnectionFailed, .serverCertificateHasBadDate,
                 .serverCertificateNotYetValid, .serverCertificateHasUnknownRoot:
                notice = "iPad HTTPS certificate trust failed (network error \(error.errorCode))."
            case .cannotConnectToHost, .cannotFindHost, .notConnectedToInternet, .networkConnectionLost:
                notice = "Could not contact localhost HTTPS service (network error \(error.errorCode))."
            case .timedOut:
                notice = "Faculty HTTPS login timed out."
            default:
                notice = "Login transport failed (network error \(error.errorCode))."
            }
        } catch {
            accessSession = nil
            notice = "Faculty login failed before receiving a valid server response."
        }
    }

    @MainActor
    private func signOut() {
        let existing = accessSession
        accessSession = nil
        assignedSessionID = ""
        password = ""
        privacyAcknowledged = false
        notice = "Signed out locally. A connected Zoom meeting must be left separately."
        if let existing, let origin = URL(string: httpsOrigin) {
            Task {
                if let client = try? HTTPSFacultyPasswordLoginClient(apiOrigin: origin) {
                    try? await client.logout(accessToken: existing.accessToken)
                }
            }
        }
    }

    @MainActor
    private func joinAuthorizedMeeting() async {
        guard canRequestJoin, let accessSession else { return }
        requestingJoin = true
        defer { requestingJoin = false }

        do {
            guard let origin = URL(string: httpsOrigin) else {
                notice = "A trusted HTTPS backend URL is required."
                return
            }
            let client = try HTTPSFacultyJoinTicketClient(apiOrigin: origin)
            let ticket = try await client.fetchAssignedMeeting(
                sessionID: assignedSessionID.trimmingCharacters(in: .whitespacesAndNewlines),
                facultyAccessToken: accessSession.accessToken
            )
            // Do not initiate an SDK join if faculty signed out or the
            // in-memory login changed while the HTTPS request was in flight.
            guard self.accessSession?.accessToken == accessSession.accessToken else {
                notice = "Sign in again before joining a meeting."
                return
            }
            notice = "The backend authorized this session. Waiting for Zoom's meeting callback."
            meeting.joinAssignedMeeting(ticket)
            if meeting.connection == .failed {
                notice = meeting.statusMessage
            }
        } catch FacultyJoinTicketError.authenticationRequired {
            self.accessSession = nil
            notice = "Your login expired. Please sign in again."
        } catch FacultyJoinTicketError.meetingAccessDenied {
            notice = "The server denied this class. Use ipad-sandbox-class (not the Zoom Meeting number), then check assignment time."
        } catch {
            notice = "The join ticket could not be issued. Verify the backend and assignment."
        }
    }
}
