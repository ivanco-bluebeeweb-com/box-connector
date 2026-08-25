# UI Component Plan — Box Connector

Follows the recorded UI standard: every input has an explicit label (not
just a placeholder), placeholders are contextually specific, the form
container is stretched to the sidebar's full width with its contents
stretched inside it, and no instruction text is duplicated between the
sidebar and the "How do I connect?" modal.

## Left sidebar (`panels.py`, slot="left")
- Not connected: `ui.Button` "Как подключить?" (ghost, opens overlay
  `box_connect_help`) THEN a `ui.Form(action="connect_box",
  submit_label="Подключить")` containing labeled fields for Label,
  Client ID, Client Secret, Enterprise ID (each wrapped via `_field()`).
- Connected: connection summary card-free stack (label + enterprise id),
  quick-nav buttons to center panels (Folders, Search, Audit), then the
  "App settings" button pinned last.

## Overlay help (`box_connect_help`, slot="overlay")
Step-by-step Box Custom App / CCG creation instructions (see
IDEAL_ONBOARDING.md) — the ONLY place these steps live.

## App settings (`panels_settings.py`, slot="center", center_overlay=True)
List of connected enterprises with a "Отключить" destructive button per
row. This is the only place disconnect lives.

## Center panels (`panels_center.py`)
- `box_folders` — root folder contents as `ui.DataTable` (name, type,
  size, modified) or `ui.Empty(icon="Folder")` when empty.
- `box_search` — placeholder empty state pointing users to chat for
  `search_files` (Box search needs a query; no meaningful default view).
- `box_audit` — `audit_content_health` findings table or
  `ui.Empty(icon="ShieldCheck")` when clean.

## Component conventions locked in (systemic, apply to every future app)
- `ui.Alert(type=..., message=...)` — never `variant=`.
- `ui.Button` never `type="submit"` (Form handles submission via
  `action=`).
- `ui.Input`/`ui.Select`/`ui.Password` always wrapped by `_field(label,
  node)` — never bare, never placeholder-only.
- `ui.DataTable` never takes `empty_text=`; branch to `ui.Empty()` first.
- `ui.Form` always uses `action="<tool_name>"` + `submit_label=`, never
  `on_submit=ui.Call(...)`.
