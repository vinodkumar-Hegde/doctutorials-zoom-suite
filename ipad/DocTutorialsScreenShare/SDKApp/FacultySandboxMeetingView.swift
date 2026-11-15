import SwiftUI

/// Actual first-party sandbox faculty login + authorized Meeting SDK join UI.
/// Built ONLY by project-sdk.yml. No mock faculty login, no fake in-meeting
/// status, and no Zoom host credentials or app secrets in the binary.
///
/// A trusted HTTPS DocTutorials backend must be deployed before login works.
/// The backend, never this iPad view, decides which session may be joined.
struct FacultySandboxMeetingView: View {
    @StateObject private var meeting = ZoomMeetingJoinAdapter()

    // The authoritative backend is Windows-hosted. Never default to Mac localhost;
    // the trusted HTTPS origin can be supplied by the deployment configuration.
    @State private var httpsOrigin = Bundle.main.object(forInfoDictionaryKey: "DocTutorialsBackendURL") as? String ?? ""
    @State private var facultyID = "sandbox-faculty"
    @State private var password = ""
    // No fabricated internal session. The backend returns actual Admin assignments.
    @State private var assignedSessionID = ""
    @State private var assignedSessions: [AssignedFacultySession] = []
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

                if assignedSessions.isEmpty {
                    Text("No assigned class loaded from the Windows Admin backend.")
                        .foregroundStyle(.secondary)
                } else {
                    Picker("Assigned class", selection: $assignedSessionID) {
                        ForEach(assignedSessions) { item in
                            Text("\(item.course) · \(item.subject) · \(item.topic)")
                                .tag(item.sessionId)
                        }
                    }
                    .accessibilityIdentifier("assignedSessionID")
                }
                Button("Refresh assigned classes") {
                    if let accessSession {
                        Task { await refreshAssignedSessions(accessSession: accessSession) }
                    }
                }
                .disabled(!isAuthenticated)
                Text("The class list is provided by DocTutorials Admin. No meeting number or manual session ID entry is required.")
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
            await refreshAssignedSessions(accessSession: granted)
            notice = assignedSessions.isEmpty
                ? "Signed in, but no assigned class is available in the Windows backend."
                : "Signed in. Select your assigned class and join."
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
        assignedSessions = []
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
    private func refreshAssignedSessions(accessSession: FacultyAccessSession) async {
        guard let base = URL(string: httpsOrigin),
              let parts = URLComponents(url: base, resolvingAgainstBaseURL: false),
              parts.scheme == "https", parts.host != nil,
              parts.user == nil, parts.password == nil,
              parts.query == nil, parts.fragment == nil,
              parts.path == "" || parts.path == "/" else {
            notice = "Enter the trusted Windows DocTutorials HTTPS backend URL."
            return
        }
        let url = base.appendingPathComponent("api").appendingPathComponent("me").appendingPathComponent("sessions")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 15
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("Bearer \(accessSession.accessToken)", forHTTPHeaderField: "Authorization")
        let session = URLSession(configuration: .ephemeral, delegate: RejectAssignmentRedirects(), delegateQueue: nil)
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse,
                  http.statusCode == 200, data.count <= 65536,
                  let decoded = try? JSONDecoder().decode(AssignedFacultySessionsResponse.self, from: data),
                  self.accessSession?.accessToken == accessSession.accessToken else {
                notice = "The Windows Admin assignment list is unavailable."
                return
            }
            let owned = decoded.sessions.filter { $0.facultyId == facultyID }
            assignedSessions = owned
            let now = Int(Date().timeIntervalSince1970)
            if let current = owned.first(where: { $0.startsAt - 900 <= now && now < $0.endsAt + 900 }) {
                assignedSessionID = current.sessionId
            } else {
                assignedSessionID = owned.first?.sessionId ?? ""
            }
        } catch {
            assignedSessions = []
            assignedSessionID = ""
            notice = "Could not load assignments from the Windows DocTutorials backend."
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
            notice = "The Windows Admin backend denied this assigned class. Refresh the assigned class list."
        } catch {
            notice = "The join ticket could not be issued. Verify the backend and assignment."
        }
    }
}

private struct AssignedFacultySessionsResponse: Decodable {
    let sessions: [AssignedFacultySession]
}

private struct AssignedFacultySession: Decodable, Identifiable {
    let sessionId: String
    let facultyId: String
    let course: String
    let subject: String
    let topic: String
    let startsAt: Int
    let endsAt: Int
    var id: String { sessionId }
}

private final class RejectAssignmentRedirects: NSObject, URLSessionTaskDelegate {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}
