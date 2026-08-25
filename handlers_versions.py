"""File version handlers for Box Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    BoxFileVersion, DeleteResult, DeleteVersionParams, FileIdParams,
    PromoteVersionParams, VersionList,
)


@chat.function(
    "list_file_versions",
    action_type="read",
    event="box-connector.list_file_versions",
    data_model=VersionList,
    description="List the saved versions of a file.",
)
async def fn_list_file_versions(ctx, params: FileIdParams) -> ActionResult:
    """List saved versions of a Box file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/files/{params.file_id}/versions")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    versions = [
        BoxFileVersion(
            version_id=v.get("id", ""),
            size_bytes=int(v.get("size", 0) or 0),
            modified_at=v.get("modified_at", "") or "",
            modified_by=((v.get("modified_by") or {}).get("name", "")) or "",
        )
        for v in (data or {}).get("entries", [])
    ]
    return ActionResult.success(data=VersionList(versions=versions).model_dump(), summary=f"{len(versions)} version(s) found.")


@chat.function(
    "promote_file_version",
    action_type="write",
    event="box-connector.promote_file_version",
    data_model=BoxFileVersion,
    description="Promote a previous file version to be the current version (Box keeps history rather than truly reverting).",
)
async def fn_promote_file_version(ctx, params: PromoteVersionParams) -> ActionResult:
    """Promote an older version of a Box file to current."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"type": "file_version", "id": params.version_id}
    try:
        data = await client.request("POST", f"/files/{params.file_id}/versions/current", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=BoxFileVersion(version_id=data.get("id", ""), size_bytes=int(data.get("size", 0) or 0), modified_at=data.get("modified_at", "") or "", modified_by="").model_dump(),
        summary="Version promoted to current.",
    )


@chat.function(
    "delete_file_version",
    action_type="write",
    event="box-connector.delete_file_version",
    data_model=DeleteResult,
    description="Move a specific file version to Trash.",
)
async def fn_delete_file_version(ctx, params: DeleteVersionParams) -> ActionResult:
    """Delete one version of a Box file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/files/{params.file_id}/versions/{params.version_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.version_id).model_dump(), summary="Version deleted.")
