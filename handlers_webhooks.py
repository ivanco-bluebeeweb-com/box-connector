"""Webhook and content-health audit handlers for Box Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import box_client as bc
from app import chat
from handlers_connection import _client_for, _resolve_connection
from schemas import (
    AuditContentParams, BoxWebhook, ConnectionRefParams, ContentAudit,
    ContentAuditFinding, CreateWebhookParams, DeleteResult,
    WebhookIdParams, WebhookList,
)


def _webhook_entity(w: dict) -> BoxWebhook:
    target = w.get("target") or {}
    return BoxWebhook(
        webhook_id=w.get("id", ""),
        target_type=target.get("type", ""),
        target_id=target.get("id", ""),
        address=w.get("address", ""),
        triggers=w.get("triggers", []) or [],
    )


@chat.function(
    "create_webhook",
    action_type="write",
    event="box-connector.create_webhook",
    data_model=BoxWebhook,
    description="Subscribe to change events on a file or folder -- Box will POST to your HTTPS endpoint when those events occur.",
)
async def fn_create_webhook(ctx, params: CreateWebhookParams) -> ActionResult:
    """Create a Box webhook on a file or folder."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    body = {
        "target": {"type": params.target_type, "id": params.target_id},
        "address": params.address,
        "triggers": params.triggers,
    }
    try:
        data = await client.request("POST", "/webhooks", json_body=body)
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=_webhook_entity(data).model_dump(), summary="Webhook created.")


@chat.function(
    "list_webhooks",
    action_type="read",
    event="box-connector.list_webhooks",
    data_model=WebhookList,
    description="List active change-event webhooks configured on the connected enterprise.",
)
async def fn_list_webhooks(ctx, params: ConnectionRefParams) -> ActionResult:
    """List active Box webhooks."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        data = await client.request("GET", "/webhooks")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    webhooks = [_webhook_entity(w) for w in (data or {}).get("entries", [])]
    return ActionResult.success(data=WebhookList(webhooks=webhooks).model_dump(), summary=f"{len(webhooks)} webhook(s) found.")


@chat.function(
    "delete_webhook",
    action_type="write",
    event="box-connector.delete_webhook",
    data_model=DeleteResult,
    description="Permanently delete a webhook subscription. Cannot be undone.",
)
async def fn_delete_webhook(ctx, params: WebhookIdParams) -> ActionResult:
    """Delete a Box webhook subscription."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    try:
        await client.request("DELETE", f"/webhooks/{params.webhook_id}")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=DeleteResult(deleted=True).model_dump(), summary="Webhook deleted.")


@chat.function(
    "audit_content_health",
    action_type="read",
    event="box-connector.audit_content_health",
    data_model=ContentAudit,
    description="Scan a folder for content-health issues: shared links on files that have not been modified recently, empty (0-byte) files, and webhooks with no event triggers configured.",
)
async def fn_audit_content_health(ctx, params: AuditContentParams) -> ActionResult:
    """Scan a Box folder and its webhooks for content-health issues."""
    conn = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(conn)
    findings: list[ContentAuditFinding] = []
    try:
        items_data = await client.request(
            "GET", f"/folders/{params.folder_id}/items",
            query={"limit": 1000, "fields": "id,name,type,size,modified_at,shared_link"},
        )
        files = [it for it in (items_data or {}).get("entries", []) if it.get("type") == "file"]
        for f in files:
            name = f.get("name", "")
            modified = f.get("modified_at", "") or ""
            if f.get("shared_link"):
                findings.append(ContentAuditFinding(
                    finding_type="stale_shared_link", item_name=name,
                    detail=f"Shared link active but the file has not been modified since {modified}.",
                ))
        for f in files:
            if int(f.get("size", 0) or 0) == 0:
                findings.append(ContentAuditFinding(
                    finding_type="empty_file", item_name=f.get("name", ""),
                    detail="File has 0 bytes.",
                ))
        webhooks_data = await client.request("GET", "/webhooks")
        for w in (webhooks_data or {}).get("entries", []):
            if not w.get("triggers"):
                findings.append(ContentAuditFinding(
                    finding_type="webhook_no_triggers", item_name=w.get("id", ""),
                    detail="Webhook has no event triggers configured -- it will never fire.",
                ))
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    return ActionResult.success(data=ContentAudit(findings=findings).model_dump(), summary=f"{len(findings)} finding(s).")
