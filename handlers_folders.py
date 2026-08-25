"""Folder handlers for Box Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    BoxFolder, CreateFolderParams, DeleteFolderParams, DeleteResult,
    FolderIdParams, RenameOrMoveFolderParams,
)


def _folder_entity(f: dict) -> BoxFolder:
    return BoxFolder(
        folder_id=f.get("id", ""),
        name=f.get("name", ""),
        parent_id=(f.get("parent") or {}).get("id", "") or "",
        item_count=int((f.get("item_collection") or {}).get("total_count", 0) or 0),
        modified_at=f.get("modified_at", "") or "",
        owned_by=((f.get("owned_by") or {}).get("name", "")) or "",
    )


@chat.function(
    "get_folder",
    action_type="read",
    event="box-connector.get_folder",
    data_model=BoxFolder,
    description="Read one Box folder's metadata in full, including item count and owner.",
)
async def fn_get_folder(ctx, params: FolderIdParams) -> ActionResult:
    """Read one Box folder's metadata."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/folders/{params.folder_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_folder_entity(data).model_dump(), summary=f"Folder '{data.get('name', '')}' loaded.")


@chat.function(
    "create_folder",
    action_type="write",
    event="box-connector.create_folder",
    data_model=BoxFolder,
    description="Create a new folder inside a parent folder.",
)
async def fn_create_folder(ctx, params: CreateFolderParams) -> ActionResult:
    """Create a new Box folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"name": params.name, "parent": {"id": params.parent_folder_id}}
    try:
        data = await client.request("POST", "/folders", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_folder_entity(data).model_dump(), summary=f"Folder '{params.name}' created.")


@chat.function(
    "rename_or_move_folder",
    action_type="write",
    event="box-connector.rename_or_move_folder",
    data_model=BoxFolder,
    description="Rename a folder and/or move it to a different parent folder.",
)
async def fn_rename_or_move_folder(ctx, params: RenameOrMoveFolderParams) -> ActionResult:
    """Rename and/or move an existing Box folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body: dict = {}
    if params.name:
        body["name"] = params.name
    if params.new_parent_folder_id:
        body["parent"] = {"id": params.new_parent_folder_id}
    if not body:
        return ActionResult.error("Provide a new name and/or a new parent folder id.")
    try:
        data = await client.request("PUT", f"/folders/{params.folder_id}", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_folder_entity(data).model_dump(), summary="Folder updated.")


@chat.function(
    "delete_folder",
    action_type="write",
    event="box-connector.delete_folder",
    data_model=DeleteResult,
    description="Permanently delete a folder. Box keeps it recoverable in Trash for a limited retention window; this cannot be undone through this connector.",
)
async def fn_delete_folder(ctx, params: DeleteFolderParams) -> ActionResult:
    """Delete a Box folder (recursively if requested)."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request(
            "DELETE", f"/folders/{params.folder_id}",
            query={"recursive": "true" if params.recursive else "false"},
        )
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.folder_id).model_dump(), summary="Folder deleted.")
