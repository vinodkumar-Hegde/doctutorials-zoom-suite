import SwiftUI

@main
struct DocTutorialsScreenShareApp: App {
    var body: some Scene {
        WindowGroup {
            #if ZOOM_MEETING_SDK_ENABLED
            FacultySandboxMeetingView()
            #else
            ScreenShareHomeView()
            #endif
        }
    }
}
