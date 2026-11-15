# Existing Admin assignment adapter (Windows central)

The prior Windows-only class-entry form was a duplicate of the existing DocTutorials Admin session registry, and has been removed. The controller's `GET /api/sessions` now uses a read-only `ExistingAdminSessions` adapter for the original schema: `~/.config/doctutorials/demo-live-sessions.sqlite3` (override with `DOCTUTORIALS_ADMIN_DB`). No Mac bridge, new Windows session entry or fabricated assignment is involved.

Only seven allowlisted columns are selected: `session_id`, `faculty_id`, `course`, `subject`, `topic`, `starts_at`, and `ends_at`. The UI does not receive meeting IDs or passcodes. The prior local Windows scheduler and its database are retained without deletion to protect existing test work, but not used by the default controller. See `README-WINDOWS.md` for the one-time schedule-only export/migration steps.

**Still pending:** converting the original Admin/Faculty portal to an authoritative Windows-hosted application (instead of copying a snapshot); joining Zoom meetings; actual media extraction/formatting; four-channel live acceptance; full faculty/iPad and NAS workflows. An existing Admin schedule entry is not proof a class is live or being recorded.
