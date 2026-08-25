"""File handlers (list/get/upload/download/update/delete/copy/search) for Box Connector."""
from __future__ import annotations

import base64

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    BoxFile, CopyFileParams, DeleteFileParams, DeleteResult,
    DownloadFileParams, DownloadResult, FileIdParams, FolderItem,
    FolderItemList, ListFolderItemsParams, SearchFilesParams,
    UpdateFileParams, UploadFileParams, UploadResult,
)


def _file_entity(f: dict) -> BoxFile:
    return BoxFile(
        file_id=f.get("id", ""),
        name=f.get("name", ""),
        size_bytes=int(f.get("size", 0) or 0),
        extension=f.get("extension", "") or "",
        modified_at=f.get("modified_at", "") or "",
        modified_by=((f.get("modified_by") or {}).get("name", "")) or "",
        shared_link=((f.get("shared_link") or {}).get("url", "")) or "",
    )


def _item_entity(it: dict) -> FolderItem:
    return FolderItem(
        item_id=it.get("id", ""),
        name=it.get("name", ""),
        item_type=it.get("type", ""),
        size_bytes=int(it.get("size", 0) or 0),
        modified_at=it.get("modified_at", "") or "",
    )


@chat.function(
    "list_folder_items",
    action_type="read",
    event="box-connector.list_folder_items",
    data_model=FolderItemList,
    description="List files and subfolders inside a Box folder.",
)
async def fn_list_folder_items(ctx, params: ListFolderItemsParams) -> ActionResult:
    """List the contents of a Box folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request(
            "GET", f"/folders/{params.folder_id}/items",
            query={"limit": min(max(params.limit, 1), 1000), "fields": "id,name,type,size,modified_at"},
        )
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    items = [_item_entity(it) for it in (data or {}).get("entries", [])]
    return ActionResult.success(data=FolderItemList(items=items).model_dump(), summary=f"{len(items)} item(s) found.")


@chat.function(
    "get_file",
    action_type="read",
    event="box-connector.get_file",
    data_model=BoxFile,
    description="Read one Box file's metadata in full.",
)
async def fn_get_file(ctx, params: FileIdParams) -> ActionResult:
    """Read one Box file's metadata."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/files/{params.file_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_file_entity(data).model_dump(), summary=f"File '{data.get('name', '')}' loaded.")


@chat.function(
    "download_file",
    action_type="read",
    event="box-connector.download_file",
    data_model=DownloadResult,
    description="Download a file's content, base64-encoded.",
)
async def fn_download_file(ctx, params: DownloadFileParams) -> ActionResult:
    """Download a Box file's raw content."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        meta = await client.request("GET", f"/files/{params.file_id}")
        content = await client.download(params.file_id)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(
        data=DownloadResult(name=meta.get("name", ""), content_base64=base64.b64encode(content).decode(), content_type="application/octet-stream").model_dump(),
        summary=f"Downloaded '{meta.get('name', '')}' ({len(content)} bytes).",
    )


@chat.function(
    "upload_file",
    action_type="write",
    event="box-connector.upload_file",
    data_model=UploadResult,
    description="Upload a new file (base64-encoded content) into a folder.",
)
async def fn_upload_file(ctx, params: UploadFileParams) -> ActionResult:
    """Upload a new file into a Box folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        raw = base64.b64decode(params.content_base64)
    except Exception:
        return ActionResult.error("content_base64 is not valid base64.")
    try:
        data = await client.upload(params.name, params.folder_id, raw)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    entry = data or {}
    return ActionResult.success(
        data=UploadResult(file_id=entry.get("id", ""), name=entry.get("name", params.name)).model_dump(),
        summary=f"'{params.name}' uploaded.",
    )


@chat.function(
    "update_file",
    action_type="write",
    event="box-connector.update_file",
    data_model=BoxFile,
    description="Rename a file and/or move it to a different folder.",
)
async def fn_update_file(ctx, params: UpdateFileParams) -> ActionResult:
    """Rename and/or move an existing Box file."""
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
        data = await client.request("PUT", f"/files/{params.file_id}", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_file_entity(data).model_dump(), summary="File updated.")


@chat.function(
    "copy_file",
    action_type="write",
    event="box-connector.copy_file",
    data_model=BoxFile,
    description="Copy a file into a (possibly different) folder.",
)
async def fn_copy_file(ctx, params: CopyFileParams) -> ActionResult:
    """Copy a Box file into a target folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {"parent": {"id": params.target_folder_id}}
    if params.new_name:
        body["name"] = params.new_name
    try:
        data = await client.request("POST", f"/files/{params.file_id}/copy", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_file_entity(data).model_dump(), summary="File copied.")


@chat.function(
    "delete_file",
    action_type="write",
    event="box-connector.delete_file",
    data_model=DeleteResult,
    description="Permanently delete a file. Box keeps it recoverable in Trash for a limited retention window; this cannot be undone through this connector.",
)
async def fn_delete_file(ctx, params: DeleteFileParams) -> ActionResult:
    """Delete a Box file."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/files/{params.file_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True, item_id=params.file_id).model_dump(), summary="File deleted.")


@chat.function(
    "search_files",
    action_type="read",
    event="box-connector.search_files",
    data_model=FolderItemList,
    description="Search files and folders across the connected Box enterprise by free-text query.",
)
async def fn_search_files(ctx, params: SearchFilesParams) -> ActionResult:
    """Full-text search across the connected Box enterprise."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/search", query={"query": params.query, "limit": min(max(params.limit, 1), 200)})
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    items = [_item_entity(it) for it in (data or {}).get("entries", [])]
    return ActionResult.success(data=FolderItemList(items=items).model_dump(), summary=f"{len(items)} result(s) found.")
