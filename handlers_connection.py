"""Connection management for Box Connector."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import box_client as bc
from app import chat, ext
from schemas import (
    BoxConnection, ConnectBoxParams, ConnectionList,
    DisconnectBoxParams, NoParams,
)

_SECRET_NAME = "box_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> BoxConnection:
    return BoxConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or c.get("enterprise_id", ""),
        enterprise_id=c.get("enterprise_id", ""),
    )


def _client_for(c: dict) -> bc.BoxClient:
    return bc.BoxClient(
        client_id=c.get("client_id", ""),
        client_secret=c.get("client_secret", ""),
        enterprise_id=c.get("enterprise_id", ""),
        as_user_id=c.get("default_as_user_id", ""),
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise bc.BoxError("No Box enterprise connected yet. Use connect_box first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise bc.BoxError(f"No connection found with id '{connection_id}'.")
    return connections[0]


@chat.function(
    "connect_box",
    action_type="write",
    event="box-connector.connect_box",
    data_model=BoxConnection,
    description="Connect your own Box enterprise via a Custom App (Client Credentials Grant): Client ID, Client Secret, and Enterprise ID.",
)
async def fn_connect_box(ctx, params: ConnectBoxParams) -> ActionResult:
    """Validate and save a new Box enterprise connection."""
    client = bc.BoxClient(
        client_id=params.client_id,
        client_secret=params.client_secret,
        enterprise_id=params.enterprise_id,
        as_user_id=params.default_as_user_id,
    )
    try:
        me = await client.request("GET", "/users/me")
    except bc.BoxError as exc:
        return ActionResult.error(str(exc))
    connections = await _load_connections(ctx)
    record = {
        "id": str(uuid.uuid4()),
        "label": params.label or params.enterprise_id,
        "client_id": params.client_id,
        "client_secret": params.client_secret,
        "enterprise_id": params.enterprise_id,
        "default_as_user_id": params.default_as_user_id,
    }
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(
        data=_connection_entity(record).model_dump(),
        summary=f"Box enterprise '{record['label']}' connected (service account: {me.get('name', 'unknown')}).",
    )


@chat.function(
    "disconnect_box",
    action_type="write",
    event="box-connector.disconnect_box",
    description="Disconnect a Box enterprise: deletes the saved Custom App credentials. Nothing in Box itself is changed.",
)
async def fn_disconnect_box(ctx, params: DisconnectBoxParams) -> ActionResult:
    """Remove a saved Box enterprise connection."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No connection found with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data={"deleted": True}, summary="Box enterprise disconnected.")


@chat.function(
    "list_connections",
    action_type="read",
    data_model=ConnectionList,
    description="List the connected Box enterprises.",
)
async def fn_list_connections(ctx, params: NoParams) -> ActionResult:
    """List saved Box enterprise connections (no secrets exposed)."""
    connections = await _load_connections(ctx)
    return ActionResult.success(
        data=ConnectionList(connections=[_connection_entity(c) for c in connections]).model_dump(),
        summary=f"{len(connections)} Box enterprise(s) connected.",
    )
