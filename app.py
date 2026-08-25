"""Box Connector extension declaration.

Box is managed via the Box Platform API v2.0 (https://api.box.com/2.0/*)
using a Custom App with Server Authentication (Client Credentials Grant),
authenticating as the enterprise Service Account by default -- same
client-credentials pattern as Microsoft SharePoint / Entra ID / Dynamics
365 Connectors in this portfolio.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "box-connector",
    version="0.1.0",
    display_name="Box",
    description=(
        "Connect your own Box enterprise via a Custom App (Client "
        "Credentials Grant) to manage Folders, Files, Versions, Search, "
        "Collaborations, Shared Links, Comments, Tasks, Metadata "
        "Templates, and Webhooks."
    ),
    icon="icon.svg",
    capabilities=["box:read", "box:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="box",
    description=(
        "Box Connector — manage Folders, Files, Versions, Search, "
        "Collaborations, Shared Links, Comments, Tasks, Metadata "
        "Templates, and Webhooks in a connected Box enterprise."
    ),
)

ext.secret(
    "box_connections",
    "JSON list of connected Box enterprises and encrypted Custom App (Client Credentials Grant) credentials. Managed only through connect_box and disconnect_box.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Box enterprise connection is saved."""
    import json

    raw = await ctx.secrets.get("box_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    ok = bool(connections)
    return {
        "ok": ok,
        "message": (
            f"{len(connections)} Box enterprise(s) connected"
            if ok else "No Box enterprise connected yet"
        ),
    }
