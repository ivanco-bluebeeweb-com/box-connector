"""Metadata template handlers for Box Connector."""
from __future__ import annotations

import json

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    ConnectionRefParams, DeleteMetadataParams, GetMetadataParams,
    MetadataInstance, MetadataTemplate, MetadataTemplateList,
    SetMetadataParams,
)


@chat.function(
    "list_metadata_templates",
    action_type="read",
    event="box-connector.list_metadata_templates",
    data_model=MetadataTemplateList,
    description="List metadata templates defined on the connected enterprise.",
)
async def fn_list_metadata_templates(ctx, params: ConnectionRefParams) -> ActionResult:
    """List enterprise metadata templates."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/metadata_templates/enterprise")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    templates = [
        MetadataTemplate(
            template_key=t.get("templateKey", ""),
            display_name=t.get("displayName", ""),
            scope=t.get("scope", ""),
            field_count=len(t.get("fields", []) or []),
        )
        for t in (data or {}).get("entries", [])
    ]
    return ActionResult.success(data=MetadataTemplateList(templates=templates).model_dump(), summary=f"{len(templates)} template(s) found.")


@chat.function(
    "get_metadata",
    action_type="read",
    event="box-connector.get_metadata",
    data_model=MetadataInstance,
    description="Read the metadata instance of a given template attached to a file.",
)
async def fn_get_metadata(ctx, params: GetMetadataParams) -> ActionResult:
    """Read a Box file's metadata instance for one template."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", f"/files/{params.file_id}/metadata/{params.scope}/{params.template_key}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    fields = {k: v for k, v in (data or {}).items() if not k.startswith("$")}
    return ActionResult.success(data=MetadataInstance(template_key=params.template_key, fields=fields).model_dump(), summary="Metadata loaded.")


@chat.function(
    "set_metadata",
    action_type="write",
    event="box-connector.set_metadata",
    data_model=MetadataInstance,
    description="Create or update a metadata instance of a given template on a file, from a JSON object of field values.",
)
async def fn_set_metadata(ctx, params: SetMetadataParams) -> ActionResult:
    """Create or update a Box file's metadata instance."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        fields = json.loads(params.fields_json)
    except (TypeError, ValueError) as exc:
        return ActionResult.error(f"fields_json is not valid JSON: {exc}")
    path = f"/files/{params.file_id}/metadata/{params.scope}/{params.template_key}"
    try:
        try:
            data = await client.request("POST", path, json_body=fields)
        except bc.BoxError as exc:
            if "already exists" in str(exc).lower() or getattr(exc, "retryable", False) is False:
                ops = [{"op": "replace", "path": f"/{k}", "value": v} for k, v in fields.items()]
                data = await client.request("PUT", path, json_body=ops, content_type="application/json-patch+json")
            else:
                raise
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    out_fields = {k: v for k, v in (data or {}).items() if not k.startswith("$")}
    return ActionResult.success(data=MetadataInstance(template_key=params.template_key, fields=out_fields).model_dump(), summary="Metadata saved.")


@chat.function(
    "delete_metadata",
    action_type="write",
    event="box-connector.delete_metadata",
    description="Remove a metadata instance of a given template from a file.",
)
async def fn_delete_metadata(ctx, params: DeleteMetadataParams) -> ActionResult:
    """Delete a Box file's metadata instance."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/files/{params.file_id}/metadata/{params.scope}/{params.template_key}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data={"deleted": True}, summary="Metadata removed.")
