import SwiftUI
import ReplayKit

/// A UI-only iPad shell. It NEVER issues a Zoom join, requests a token or starts a stream.
/// The Zoom Meeting SDK adapter, backend faculty identity and ReplayKit upload
/// extension must be integrated and verified before enabling the broadcast picker.
struct ScreenShareHomeView: View {
    @State private var previewSession = false
    @State private var privacyAcknowledged = false
    @State private var connection: MeetingConnectionState = .disconnected
    @State private var zoomSharePermissionConfirmed = false

    private var mayBroadcast: Bool {
        ScreenSharePolicy.mayOfferBroadcast(
            connection: connection,
            privacyAcknowledged: privacyAcknowledged,
            zoomSharePermissionConfirmed: zoomSharePermissionConfirmed
        )
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    header
                    sessionCard
                    meetingCard
                    shareCard
                    privacyCard
                    footer
                }
                .frame(maxWidth: 760)
                .padding(.horizontal, 24)
                .padding(.vertical, 28)
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
                .font(.title2.weight(.bold))
            Text("Teach from your iPad")
                .font(.largeTitle.weight(.bold))
            Text("Connect to your assigned Zoom Meeting, then share Goodnotes or another app with Apple Pencil.")
                .foregroundStyle(.secondary)
            Label("Development preview — no meeting is joined or broadcast", systemImage: "hammer")
                .font(.footnote.weight(.medium))
                .foregroundStyle(.orange)
        }
    }

    private var sessionCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Assigned class", systemImage: "calendar")
                    .font(.headline)
                Text(previewSession ? "Sample Lecture • UI demonstration" : "No class loaded")
                    .font(.title3.weight(.semibold))
                Text(previewSession
                     ? "This is sample data only; not a real assignment or Zoom invitation."
                     : "Faculty sign-in and assigned-session retrieval will connect here.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button(previewSession ? "Clear demonstration" : "Preview sample class") {
                    previewSession.toggle()
                }
                .buttonStyle(.bordered)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var meetingCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Zoom Meeting", systemImage: "video")
                    .font(.headline)
                Label(ScreenSharePolicy.statusText(for: connection), systemImage: "circle.dashed")
                    .foregroundStyle(.secondary)
                Text("iPad microphone and camera will be off by default when meeting join is implemented.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Button("Join assigned meeting") { }
                    .buttonStyle(.borderedProminent)
                    .disabled(true) // Not wired to an SDK or authorized backend yet.
                Text("Unavailable until Meeting SDK authorization, participant join and callbacks are verified.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var shareCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Present your iPad screen", systemImage: "rectangle.on.rectangle.angled")
                    .font(.headline)
                Text("Open Goodnotes after starting an Apple-confirmed full-device broadcast. Other apps and notifications may be visible to attendees.")
                    .font(.subheadline)
                if mayBroadcast {
                    // This branch stays unreachable until the real SDK adapter
                    // confirms connection AND screen-share entitlement.
                    BroadcastPicker(extensionBundleID: "com.doctutorials.facultyscreen.ScreenShare")
                        .frame(width: 70, height: 70)
                    Text("Tap the broadcast icon and confirm in Apple's dialog.")
                        .font(.caption)
                } else {
                    Label("Screen broadcast unavailable until Zoom is connected and sharing is permitted.", systemImage: "lock.shield")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var privacyCard: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                Label("Before broadcasting", systemImage: "hand.raised")
                    .font(.headline)
                Text("Enable Focus / Do Not Disturb. Close personal apps and sensitive notifications. Verify you are teaching in the intended class.")
                    .font(.subheadline)
                Toggle("I understand the entire iPad screen may be shared", isOn: $privacyAcknowledged)
                    .font(.subheadline)
                Text("Apple always requires a separate, user-initiated screen broadcast confirmation.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var footer: some View {
        Text("Windows recording: deferred. Webinar support: deferred. This app cannot currently join a meeting or transmit a screen.")
            .font(.footnote)
            .foregroundStyle(.secondary)
    }
}

private struct BroadcastPicker: UIViewRepresentable {
    let extensionBundleID: String

    func makeUIView(context: Context) -> RPSystemBroadcastPickerView {
        let picker = RPSystemBroadcastPickerView(frame: .zero)
        picker.preferredExtension = extensionBundleID
        picker.showsMicrophoneButton = false // Laptop handles faculty audio.
        return picker
    }

    func updateUIView(_ uiView: RPSystemBroadcastPickerView, context: Context) {}
}
