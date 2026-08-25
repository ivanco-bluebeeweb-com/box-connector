"""Box Connector -- center panels for Folders and Content Audit."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
import handlers_files as hfi
import handlers_webhooks as hw
from app import ext
from schemas import AuditContentParams, ListFolderItemsParams


def _table_or_empty(rows, columns, empty_message, empty_icon):
    if not rows:
        return ui.Empty(message=empty_message, icon=empty_icon)
    return ui.DataTable(rows=rows, columns=columns)


@ext.panel("box_folders", slot="center", title="Folders", center_overlay=True)
async def box_folders(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Folder")
    folder_id = kwargs.get("folder_id", "0")
    result = await hfi.fn_list_folder_items(ctx, ListFolderItemsParams(folder_id=folder_id))
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not load folder")
    items = (result.data or {}).get("items", [])
    rows = [{"name": it["name"], "item_type": it["item_type"], "size_bytes": it["size_bytes"]} for it in items]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="item_type", label="Type"),
        ui.DataColumn(key="size_bytes", label="Size (bytes)"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Folder contents", level=2),
        _table_or_empty(rows, columns, "This folder is empty", "Folder"),
    ])


@ext.panel("box_audit", slot="center", title="Content audit", center_overlay=True)
async def box_audit(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    folder_id = kwargs.get("folder_id", "0")
    result = await hw.fn_audit_content_health(ctx, AuditContentParams(folder_id=folder_id))
    if not result.success:
        return ui.Alert(type="error", message=result.error or "Could not run audit")
    findings = (result.data or {}).get("findings", [])
    rows = [{"finding_type": f["finding_type"], "item_name": f["item_name"], "detail": f["detail"]} for f in findings]
    columns = [
        ui.DataColumn(key="finding_type", label="Type"),
        ui.DataColumn(key="item_name", label="Item"),
        ui.DataColumn(key="detail", label="Detail"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Content audit", level=2),
        _table_or_empty(rows, columns, "No findings -- content looks healthy", "ShieldCheck"),
    ])
