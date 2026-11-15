import Foundation

/// Secure network contract for the future authenticated faculty iPad join flow.
/// This code is deliberately NOT invoked from the current SwiftUI UI:
/// faculty login and assigned-session retrieval have not been implemented.
enum FacultyJoinTicketError: Error {
    case unsafeConfiguration
    case invalidRequest
    case authenticationRequired
    case meetingAccessDenied
    case joinServiceUnavailable
    case invalidServerResponse
}

struct HTTPSFacultyJoinTicketClient {
    private let apiOrigin: URL
    private let session: URLSession

    /// apiOrigin must be an HTTPS origin only, not a URL containing credentials,
    /// a session path, query or fragment. Never point this to localhost HTTP.
    init(apiOrigin: URL, session: URLSession = URLSession(configuration: .ephemeral)) throws {
        guard let parts = URLComponents(url: apiOrigin, resolvingAgainstBaseURL: false),
              parts.scheme?.lowercased() == "https",
              parts.host != nil,
              parts.user == nil, parts.password == nil,
              parts.query == nil, parts.fragment == nil,
              parts.path == "" || parts.path == "/" else {
            throw FacultyJoinTicketError.unsafeConfiguration
        }
        self.apiOrigin = apiOrigin
        self.session = session
    }

    /// Requests a join ticket ONLY for a server-authorized DocTutorials session.
    /// facultyAccessToken must originate from a verified faculty login flow.
    /// Do not persist or print access tokens, Zoom meeting passcodes or SDK JWTs.
    func fetchAssignedMeeting(
        sessionID: String,
        facultyAccessToken: String
    ) async throws -> AuthorizedMeetingJoinTicket {
        let allowed = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        guard (1...100).contains(sessionID.count),
              sessionID.unicodeScalars.allSatisfy({ allowed.contains($0) }),
              (20...8192).contains(facultyAccessToken.count),
              facultyAccessToken.rangeOfCharacter(from: .whitespacesAndNewlines) == nil else {
            throw FacultyJoinTicketError.invalidRequest
        }

        let url = apiOrigin
            .appendingPathComponent("api")
            .appendingPathComponent("sessions")
            .appendingPathComponent(sessionID)
            .appendingPathComponent("join")
            .appendingPathComponent("ipad")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 15
        request.setValue("Bearer \(facultyAccessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = nil

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw FacultyJoinTicketError.invalidServerResponse
        }
        switch http.statusCode {
        case 200:
            break
        case 401:
            throw FacultyJoinTicketError.authenticationRequired
        case 403:
            throw FacultyJoinTicketError.meetingAccessDenied
        default:
            throw FacultyJoinTicketError.joinServiceUnavailable
        }

        // Small, known response schema; never persist or print sensitive data.
        guard data.count <= 8192,
              let payload = try? JSONDecoder().decode(JoinTicketPayload.self, from: data),
              payload.expiresAtEpoch > Int(Date().timeIntervalSince1970) + 30 else {
            throw FacultyJoinTicketError.invalidServerResponse
        }
        let ticket = AuthorizedMeetingJoinTicket(
            meetingNumber: payload.meetingNumber,
            meetingPasscode: payload.meetingPasscode,
            displayName: payload.displayName,
            meetingSDKJWT: payload.meetingSDKJWT
        )
        guard ticket.isPlausible else {
            throw FacultyJoinTicketError.invalidServerResponse
        }
        return ticket
    }
}

private struct JoinTicketPayload: Decodable {
    let meetingNumber: String
    let meetingPasscode: String
    let displayName: String
    let meetingSDKJWT: String
    let expiresAtEpoch: Int
}
