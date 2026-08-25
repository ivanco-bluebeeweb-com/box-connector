# Discovery — Box Connector

## What is Box?
Box is an Enterprise Content Management (ECM) / cloud content management
platform: folders, files, versioning, sharing links, collaborations
(permissions), comments, tasks, and metadata templates on top of files.
Widely used for document-heavy workflows (legal, HR, sales rooms).

## Auth model chosen: Client Credentials Grant (CCG) with a Service Account
Box supports three server-to-server patterns. For a connector with no
interactive browser step (matches this portfolio's existing pattern for
SharePoint/Entra ID/Dynamics 365 — all client-credentials), the right one is:

- **Box Custom App (Server Authentication) — Client Credentials Grant**:
  requires Box Developer Console app of type "Custom App" with
  "Server Authentication (Client Credentials Grant)". Yields a
  Client ID + Client Secret + Enterprise ID. Token endpoint:
  `POST https://api.box.com/oauth2/token` with
  `grant_type=client_credentials&box_subject_type=enterprise&box_subject_id={enterprise_id}`.
  This authenticates as the enterprise's Service Account by default (a
  headless user Box auto-provisions) — sees only what's explicitly shared
  with it, OR (if admin re-authorizes with "as-user" scope) can impersonate
  users via `box_subject_type=user`. We support both: a stored
  `enterprise_id` (service-account mode) and an optional per-call
  `as_user_id` override.
  Rejected: legacy JWT app (deprecated by Box in 2025 in favor of CCG) and
  the interactive OAuth2 3-legged flow (requires a redirect/browser step —
  inconsistent with this portfolio's server-only connector pattern).

## API surface (Box Platform API v2.0, base `https://api.box.com/2.0`)
- Folders: `GET /folders/{id}`, `GET /folders/{id}/items`, `POST /folders`,
  `PUT /folders/{id}` (rename/move), `DELETE /folders/{id}`.
- Files: `GET /files/{id}`, `GET /files/{id}/content` (download),
  `POST /files/content` (upload, multipart, separate `upload.box.com`
  host), `POST /files/{id}/content` (new version), `PUT /files/{id}`
  (rename/move/description), `DELETE /files/{id}`, `POST /files/{id}/copy`.
- Versions: `GET /files/{id}/versions`, `POST /files/{id}/versions/current`
  (promote/restore a version).
  DELETE `/files/{id}/versions/{version_id}` (move a version to trash).
- Search: `GET /search?query=...` (full-text + metadata filters).
- Collaborations (permissions): `GET /folders/{id}/collaborations`,
  `POST /collaborations` (invite by email/user id with a role), `PUT
  /collaborations/{id}` (change role), `DELETE /collaborations/{id}`.
- Shared links: `PUT /files/{id}` with `shared_link` object (Box models
  shared links as a property update, not a separate resource).
- Comments: `GET /files/{id}/comments`, `POST /comments`.
- Tasks: `GET /files/{id}/tasks`, `POST /tasks`, `PUT
  /task_assignments/{id}` (complete/reject).
- Metadata templates: `GET /metadata_templates/enterprise`, `POST
  /files/{id}/metadata/{scope}/{template}` (apply structured metadata).
- Webhooks: `GET/POST/DELETE /webhooks` (event-driven push notifications
  — `FILE.UPLOADED`, `FILE.TRASHED`, etc.).
- Users: `GET /users/me` (identity check for connect-time validation),
  `GET /users` (enterprise directory, admin-scope only).

## Rate limits & pagination
Box enforces per-app rate limits (~ per-second burst limits, varies by
endpoint class); standard practice is exponential backoff on 429. List
endpoints use `offset`/`limit` (marker-based pagination for some,
offset-based for folder items) — max `limit=1000` for folder items,
default 100.

## Known portfolio gotchas applied proactively (per systemic review)
- Client-credentials token caching (bug class from Vikunja #2356):
  cache access_token + expiry in-memory on the client instance, refresh
  only when within a safety margin of expiry.
- ui.Form must use `action=`+`submit_label=` (never `on_submit=ui.Call`).
- Every input has an explicit label (via `_field()` wrapper) plus a
  contextual placeholder — never placeholder-only.
- Left sidebar carries NO instructions duplicated in the help modal (the
  "Как подключить?" button opens an `overlay` panel exclusively).
- `ui.Alert` uses `type=`, never `variant=`. `ui.Button` never uses
  `type="submit"`. `ui.DataTable` never takes `empty_text=` — callers
  branch to `ui.Empty()` when rows is empty.
