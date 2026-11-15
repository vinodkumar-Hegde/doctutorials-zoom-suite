# Local Windows Admin — acceptance and boundaries

**Implemented:** First-party SQLite schedule hosted on the SAME Windows computer as the FFmpeg recorder controller and Storage Center. After controller login, the operator can add assigned sessions (course, subject, topic, faculty and scheduled start/end), reserve one of four recording channels, view existing assignments and cancel them. Canceled sessions remain in the audit-friendly schedule and the existing recording library is not deleted. Scheduling disallows overlapping reserved channel times and verifies inputs and auth.

**Not yet implemented:** Sync from an actual remote DocTutorials production scheduling backend, Zoom Meeting creation, Zoom SDK raw media adapter, Zoom participant join, proof of a live meeting, laptop/iPad real device end-to-end workflow, or production multi-host orchestration. The dashboard explicitly marks scheduled windows as **NOT Zoom live status** and labels synthetic channels **TEST MEDIA**.

**Local API (Admin bearer token, loopback only):** `GET /api/sessions`, `POST /api/sessions/create`, `POST /api/sessions/cancel`. Session data deliberately contains no Zoom meeting IDs, passcodes or JWTs. SQLite lives at `<storage_root>/windows-admin-sessions.sqlite3`. Stop the running controller before switching its `storage_root` to avoid confusion about data location.

**Tests:** `py -3 -m unittest discover -s tests -v` runs existing media-engine checks plus new Windows Admin schedule and HTTP authorization tests. These local tests verify no Zoom media capture.

The old Mac-to-Windows schedule-bridge utilities are obsolete for this path. They may remain in historical source for reference but are neither required nor imported by the controller.
