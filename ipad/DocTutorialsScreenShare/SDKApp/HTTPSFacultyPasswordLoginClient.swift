import Foundation

/// Local DocTutorials static-password faculty login for the Basic Zoom sandbox.
/// No third-party authentication provider. Only a server-generated,
/// short-lived bearer token is returned on successful HTTPS login.
/// Not connected to the SwiftUI screen until a trusted HTTPS backend exists.
struct FacultyAccessSession {
    let accessToken: String
    let expiresAtEpoch: Int

    var isUsable: Bool {
        (40...64).contains(accessToken.count)
            && accessToken.utf8.allSatisfy {
                ($0 >= 65 && $0 <= 90) ||
                ($0 >= 97 && $0 <= 122) ||
                ($0 >= 48 && $0 <= 57) ||
                $0 == 45 || $0 == 95
            }
            && expiresAtEpoch > Int(Date().timeIntervalSince1970) + 30
    }
}

enum FacultyPasswordLoginError: Error {
    case invalidConfiguration
    case invalidInput
    case rejectedCredentials
    case serviceUnavailable(httpStatus: Int)
    case invalidServerResponse
}

/// HTTPS-only first-party faculty login; password is sent ONLY in one POST body.
/// Caller should never persist, print or embed faculty passwords in the binary.
struct HTTPSFacultyPasswordLoginClient {
    private let apiOrigin: URL
    private let session: URLSession

    init(
        apiOrigin: URL,
        session: URLSession = URLSession(
            configuration: .ephemeral,
            delegate: RejectFacultyLoginRedirects(),
            delegateQueue: nil
        )
    ) throws {
        guard let parts = URLComponents(url: apiOrigin, resolvingAgainstBaseURL: false),
              parts.scheme?.lowercased() == "https",
              parts.host != nil,
              parts.user == nil,
              parts.password == nil,
              parts.query == nil,
              parts.fragment == nil,
              parts.path == "" || parts.path == "/" else {
            throw FacultyPasswordLoginError.invalidConfiguration
        }
        self.apiOrigin = apiOrigin
        self.session = session
    }

    /// Password must come from faculty interaction, never from Swift literals.
    func login(facultyID: String, password: String) async throws -> FacultyAccessSession {
        let allowed = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        guard (1...100).contains(facultyID.count),
              facultyID.unicodeScalars.allSatisfy({ allowed.contains($0) }),
              (16...128).contains(password.count),
              !password.contains("\n"),
              !password.contains("\r"),
              !password.contains("\0") else {
            throw FacultyPasswordLoginError.invalidInput
        }

        let url = apiOrigin
            .appendingPathComponent("api")
            .appendingPathComponent("faculty")
            .appendingPathComponent("login")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 15
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        let jsonData = try JSONEncoder().encode(
            FacultyLoginRequest(facultyId: facultyID, password: password)
        )
        guard jsonData.count <= 4096 else {
            throw FacultyPasswordLoginError.invalidInput
        }
        request.httpBody = jsonData

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw FacultyPasswordLoginError.invalidServerResponse
        }
        switch http.statusCode {
        case 200: break
        case 401: throw FacultyPasswordLoginError.rejectedCredentials
        default: throw FacultyPasswordLoginError.serviceUnavailable(httpStatus: http.statusCode)
        }
        guard data.count <= 2048,
              let payload = try? JSONDecoder().decode(FacultyLoginResponse.self, from: data),
              payload.tokenType == "Bearer" else {
            throw FacultyPasswordLoginError.invalidServerResponse
        }
        let session = FacultyAccessSession(
            accessToken: payload.accessToken,
            expiresAtEpoch: payload.expiresAtEpoch
        )
        guard session.isUsable else {
            throw FacultyPasswordLoginError.invalidServerResponse
        }
        return session
    }

    /// Discards the server-side session token; caller must also discard its
    /// own in-memory FacultyAccessSession, even if the network call fails.
    func logout(accessToken: String) async throws {
        let url = apiOrigin
            .appendingPathComponent("api")
            .appendingPathComponent("faculty")
            .appendingPathComponent("logout")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 15
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        let (_, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 204 else {
            throw FacultyPasswordLoginError.serviceUnavailable(httpStatus: (response as? HTTPURLResponse)?.statusCode ?? 0)
        }
    }
}

private struct FacultyLoginRequest: Encodable {
    let facultyId: String
    let password: String
}

private struct FacultyLoginResponse: Decodable {
    let accessToken: String
    let tokenType: String
    let expiresAtEpoch: Int
}

/// Never allow redirects while password or Bearer token is being sent.
private final class RejectFacultyLoginRedirects: NSObject, URLSessionTaskDelegate {
    func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        willPerformHTTPRedirection response: HTTPURLResponse,
        newRequest request: URLRequest,
        completionHandler: @escaping (URLRequest?) -> Void
    ) {
        completionHandler(nil)
    }
}
