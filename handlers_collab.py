"""Collaboration (permissions) and shared-link handlers for Box Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    BoxCollaboration, BoxSharedLink, ClearSharedLinkParams,
    CollaborationList, CreateCollaborationParams, CreateSharedLinkParams,
    DeleteResult, GetSharedLinkParams, ItemRefParams,
    RemoveCollaborationParams, UpdateCollaborationParams,
)


def _collab_entity(c: dict) -> BoxCollaboration:
    accessible_by = c.get("accessible_by") or {}
    return BoxCollaboration(
        collaboration_id=c.get("id", ""),
        role=c.get("role", ""),
        status=c.get("status", ""),
        accessible_by_name=accessible_by.get("name", "") or accessible_by.get("login", "") or "",
        accessible_by_type=accessible_by.get("type", ""),
    )


@chat.function(
    "list_collaborations",
    action_type="read",
    event="box-connector.list_collaborations",
    data_model=CollaborationList,
    description="List collaborators (permissions) on a folder or file.",
)
async def fn_list_collaborations(ctx, params: ItemRefParams) -> ActionResult:
    """List collaborators on a Box folder or file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    path = f"/folders/{params.item_id}/collaborations" if params.item_type == "folder" else f"/files/{params.item_id}/collaborations"
    try:
        data = await client.request("GET", path)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    collabs = [_collab_entity(c) for c in (data or {}).get("entries", [])]
    return ActionResult.success(data=CollaborationList(collaborations=collabs).model_dump(), summary=f"{len(collabs)} collaborator(s) found.")


@chat.function(
    "create_collaboration",
    action_type="write",
    event="box-connector.create_collaboration",
    data_model=BoxCollaboration,
    description="Grant a user or group access (a role: viewer, editor, co-owner, etc.) to a folder or file.",
)
async def fn_create_collaboration(ctx, params: CreateCollaborationParams) -> ActionResult:
    """Grant collaboration access on a Box item."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    item_type = "folder" if params.item_type == "folder" else "file"
    accessible_by: dict = {"type": "group" if params.grantee_type == "group" else "user"}
    if params.grantee_login:
        accessible_by["login"] = params.grantee_login
    else:
        accessible_by["id"] = params.grantee_id
    body = {"item": {"type": item_type, "id": params.item_id}, "accessible_by": accessible_by, "role": params.role}
    try:
        data = await client.request("POST", "/collaborations", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_collab_entity(data).model_dump(), summary=f"Collaboration created with role '{params.role}'.")


@chat.function(
    "update_collaboration",
    action_type="write",
    event="box-connector.update_collaboration",
    data_model=BoxCollaboration,
    description="Change an existing collaborator's role.",
)
async def fn_update_collaboration(ctx, params: UpdateCollaborationParams) -> ActionResult:
    """Change a Box collaborator's role."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("PUT", f"/collaborations/{params.collaboration_id}", json_body={"role": params.role})
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_collab_entity(data).model_dump(), summary="Collaboration role updated.")


@chat.function(
    "remove_collaboration",
    action_type="write",
    event="box-connector.remove_collaboration",
    data_model=DeleteResult,
    description="Revoke a collaborator's access to a folder or file.",
)
async def fn_remove_collaboration(ctx, params: RemoveCollaborationParams) -> ActionResult:
    """Revoke a Box collaboration."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/collaborations/{params.collaboration_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.collaboration_id).model_dump(), summary="Collaboration removed.")


@chat.function(
    "create_shared_link",
    action_type="write",
    event="box-connector.create_shared_link",
    data_model=BoxSharedLink,
    description="Create or update a shared link on a file or folder.",
)
async def fn_create_shared_link(ctx, params: CreateSharedLinkParams) -> ActionResult:
    """Create/update a Box shared link."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    path = f"/folders/{params.item_id}" if params.item_type == "folder" else f"/files/{params.item_id}"
    shared_link: dict = {"access": params.access}
    if params.can_download is not None:
        shared_link["permissions"] = {"can_download": params.can_download}
    body = {"shared_link": shared_link}
    try:
        data = await client.request("PUT", path, json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    link = data.get("shared_link") or {}
    return ActionResult.success(
        data=BoxSharedLink(url=link.get("url", ""), access=link.get("access", ""), download_url=link.get("download_url", "") or "").model_dump(),
        summary="Shared link created.",
    )


@chat.function(
    "get_shared_link",
    action_type="read",
    event="box-connector.get_shared_link",
    data_model=BoxSharedLink,
    description="Read a file or folder's current shared link, if any.",
)
async def fn_get_shared_link(ctx, params: GetSharedLinkParams) -> ActionResult:
    """Read the current shared link on a Box item."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    path = f"/folders/{params.item_id}" if params.item_type == "folder" else f"/files/{params.item_id}"
    try:
        data = await client.request("GET", path, query={"fields": "shared_link"})
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    link = data.get("shared_link") or {}
    if not link:
        return ActionResult.success(data=BoxSharedLink(url="", access="", download_url="").model_dump(), summary="No shared link set on this item.")
    return ActionResult.success(
        data=BoxSharedLink(url=link.get("url", ""), access=link.get("access", ""), download_url=link.get("download_url", "") or "").model_dump(),
        summary="Shared link loaded.",
    )


@chat.function(
    "clear_shared_link",
    action_type="write",
    event="box-connector.clear_shared_link",
    data_model=DeleteResult,
    description="Remove the shared link from a file or folder.",
)
async def fn_clear_shared_link(ctx, params: ClearSharedLinkParams) -> ActionResult:
    """Remove a Box item's shared link."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    path = f"/folders/{params.item_id}" if params.item_type == "folder" else f"/files/{params.item_id}"
    try:
        await client.request("PUT", path, json_body={"shared_link": None})
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.item_id).model_dump(), summary="Shared link removed.")
