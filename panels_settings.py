"""Box Connector -- App settings panel."""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


@ext.panel("box_settings", slot="center", title="Box settings", icon="Settings", center_overlay=True)
async def box_settings(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Text("Ни одно предприятие Box ещё не подключено.", variant="body")
    rows = []
    for c in connections:
        rows.append(ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(f"{c.get('label') or c.get('enterprise_id', '')}", variant="body"),
            ui.Button("Отключить", variant="destructive", on_click=ui.Call("disconnect_box", {"connection_id": c.get("id", "")})),
        ]))
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Подключённые предприятия", level=2),
        *rows,
    ])
