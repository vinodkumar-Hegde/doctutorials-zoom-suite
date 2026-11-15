# ADR-027 — Stop duplicate class entry; use original Admin session schema

**2026-11-15 — Development adapter, not production migration**

The Windows-local Assign Class form introduced in ADR-026 duplicated the existing DocTutorials Live Admin session registry stored in `~/.config/doctutorials/demo-live-sessions.sqlite3` on Mac. The user rightly rejected entering assigned class details again. Keeping the duplicate form would create split-brain schedules.

## Change

The Windows controller now defaults to read-only `ExistingAdminSessions`, using the original Admin schema directly. It selects seven public scheduling fields, and does not read or return meeting identifiers or passcodes. When no Admin database has been migrated, the interface explicitly shows that the original data is missing and does not offer a new fake assignment form. A schedule-only export utility prepares a SQLite copy without Zoom secrets for one-time safe transfer. It can be used when the Admin source is still on a separate Mac, without an ongoing bridge. The UI's TEST MEDIA action no longer prompts for class information.

Legacy Windows-local `LocalSessions` data and API support remain in the source for compatibility and data preservation; the default running controller uses `ExistingAdminSessions`, and create/cancel endpoints return 405 in that mode. The source file is reread whenever the dashboard polls.

## Incomplete

The export is a **snapshot**: new Mac edits will not automatically reach Windows. A one-time transfer requires operator action, and the controller cannot read the Mac disk directly. The long-term requirement is to deploy the actual Admin/Faculty session service and its authoritative database on Windows, then connect that service to a permitted live Zoom capture adapter. No real Zoom connection, live status, recording automation, or simultaneous channel capture is claimed.

## Tests

48 automated local tests PASS, including reading original Admin SQLite schema, missing/invalid database handling, no Zoom secrets in API output, read-only HTTP handling, preserving source database bytes, safe schedule-only export, and existing FFmpeg synthetic worker coverage. Windows hardware, real Admin data migration, and live Zoom recording remain untested.
