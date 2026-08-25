# Preparation — Box Connector

## Scope (locked, per standing rule "maximum functionality")
Full ECM surface: connection management, Folders, Files (CRUD +
upload/download + copy/move), Versions, Search, Collaborations
(permissions), Shared Links, Comments, Tasks, Metadata Templates,
Webhooks, and one value-add aggregated report (`audit_content_health`).

## Secrets
- `box_connections` (JSON list): `[{id, label, client_id, client_secret,
  enterprise_id, default_as_user_id}]`. Client secret never echoed back
  to chat/UI after saving.

## Handler file split (mirrors SharePoint Connector's proven layout)
- `box_client.py` — BoxClient: token cache + generic `request()` wrapper
  over `https://api.box.com/2.0`, plus a separate `upload()` helper
  hitting `https://upload.box.com/api/2.0`.
- `handlers_connection.py` — connect/disconnect/list_connections.
- `handlers_folders.py` — list/get/create/rename/move/delete folders.
- `handlers_files.py` — list items, get/download/upload/update/delete/copy
  file, search.
- `handlers_versions.py` — list/promote/delete versions.
- `handlers_collab.py` — collaborations (grant/list/update/revoke),
  shared links (create/get/remove).
- `handlers_comments_tasks.py` — comments + tasks.
- `handlers_metadata.py` — metadata templates: list templates, get/set/
  delete metadata instance on a file.
- `handlers_webhooks.py` — create/list/delete webhooks + one aggregated
  `audit_content_health` report (stale shared links >90d, files with 0
  collaborators outside owner, orphaned webhooks).
- `panels.py` / `panels_settings.py` / `panels_center.py` — UI, built
  during construction per UI_COMPONENT_PLAN.md below, not after.

## Security
- Client secret stored only in the `box_connections` secret blob, never
  logged, never returned by any read handler.
- Destructive actions (`delete_folder`, `delete_file`, `delete_webhook`,
  `revoke_collaboration`) are `action_type="write"` with clear
  irreversibility language in their descriptions.
- Enterprise-wide `list_users` intentionally NOT included in v1 scope —
  admin-only endpoint, out of scope for a content-management connector
  (avoids over-broad admin-scope requirement at install time).

## Tests / validation
- `imperal validate .` must show 0 errors before commit.
- Manual smoke: connect with a real Box Custom App CCG credential set,
  list_folders on root (id="0"), create+delete a test folder.

## Pricing plan (locked before submit_for_review, same as SharePoint)
Fixed scale {0, 8, 16, 20, 40, 60}: 0 = connect/disconnect/list_connections,
8 = reads, 16 = standard writes, 20 = higher-effort actions (upload/promote
version), 40 = audit_content_health.
