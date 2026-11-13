# Data Model and API Outline — Proposal

All IDs below are internal UUIDs unless explicitly described as Zoom IDs. Schema is **not implemented**.

## Database entities
| Entity | Core fields |
|---|---|
| `faculty_users` | id, email, display_name, status, roles |
| `zoom_host_accounts` | id, external_user_id (encrypted or protected), license_profile, enabled |
| `courses` | id, code, title |
| `subjects` | id, course_id, title |
| `sessions` | id, course_id, subject_id, topic, start_at, duration, zoom_host_id, zoom_meeting_id, kind, state |
| `session_faculty` | session_id, faculty_id, device_role, webinar_panelist_entitlement |
| `recorder_channels` | id, worker_id, zoom_host_account_id, state, last_seen_at |
| `recording_jobs` | id, session_id, channel_id, requested_state, observed_state, last_error, start_at, stop_at |
| `recording_assets` | id, job_id, source (`local`,`cloud`), path_ref, checksum, file_size, duration, verified_at, archived_at |
| `webhook_events` | event_id, event_name, meeting_uuid, received_at, processed_at, dedupe_key |
| `audit_events` | id, actor_id, action, target_type, target_id, result, at |

## Draft endpoints
- `GET /api/me/sessions` — faculty's assigned sessions.
- `POST /api/sessions` — authorized admin creates session.
- `POST /api/sessions/{id}/join/laptop` — provide short-lived authorized native Zoom join information.
- `POST /api/sessions/{id}/join/ipad` — provide authorized SDK join information (subject to Zoom panelist test).
- `POST /api/sessions/{id}/recordings/{action}` — local recording control with faculty/operator RBAC.
- `GET /api/sessions/{id}/recordings` — cloud and local states separately.
- `POST /webhooks/zoom` — signed Zoom webhook receiver.
- `POST /internal/agents/events` — signed worker event receiver.
- `GET /api/admin/channels` — four-channel live status.

## Idempotency requirements
- Deduplicate Zoom events; accept out-of-order delivery.
- A recording start command has a stable request ID and must not start duplicates.
- Recording asset uses immutable content hash and retention state.
- Every actuator response verifies observed state before success is shown.

## Privacy
Personal invitation links and signed SDK join credentials must not be stored in plaintext in logs or public APIs. Data residency, retention and deletion policies will be defined before production.
