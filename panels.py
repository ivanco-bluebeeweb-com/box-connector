"""Box Connector -- left sidebar panel.

Follows the recorded UI standard (see WEBBEE.md / UI_COMPONENT_PLAN.md):
no decorated cards in the sidebar, every input has an explicit label, the
form container stretches to the sidebar's full width with its contents
stretched inside it, and no setup instructions are duplicated between the
sidebar and the "How do I connect?" overlay.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers_connection as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="Settings", on_click=ui.Call("__panel__box_settings"),
    )


@ext.panel("box_sidebar", slot="left", title="Box")
async def box_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("Как подключить?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__box_connect_help")),
            ui.Button("Authorize Box Enterprise (OAuth 2.0)", variant="primary", size="sm", full_width=True, icon="login"),
            ui.Divider(),
            ui.Text("Or connect via Custom App Client Credentials", variant="caption"),
            ui.Form(action="connect_box", submit_label="Подключить", children=[
                ui.Stack(direction="v", gap=3, align="stretch", children=[
                    _field("Название (необязательно)", ui.Input(param_name="label", placeholder="например, Acme Corp Box")),
                    _field("Client ID", ui.Input(param_name="client_id", placeholder="из Box Developer Console > Configuration")),
                    _field("Client Secret", ui.Password(param_name="client_secret", placeholder="из Box Developer Console > Configuration")),
                    _field("Enterprise ID", ui.Input(param_name="enterprise_id", placeholder="из Box Developer Console или Admin Console")),
                    _field("User ID для имперсонации (необязательно)", ui.Input(param_name="default_as_user_id", placeholder="оставьте пустым для Service Account")),
                ]),
            ]),
        ])
    c = connections[0]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Stack(direction="v", gap=1, align="stretch", children=[
            ui.Text(c.get("label") or c.get("enterprise_id", ""), variant="body"),
            ui.Text(f"Enterprise ID: {c.get('enterprise_id', '')}", variant="caption"),
        ]),
        ui.Button("Папки", variant="secondary", size="sm", full_width=True, icon="Folder",
                  on_click=ui.Call("__panel__box_folders")),
        ui.Button("Аудит контента", variant="secondary", size="sm", full_width=True, icon="ShieldCheck",
                  on_click=ui.Call("__panel__box_audit")),
        _settings_button(),
    ])


@ext.panel("box_connect_help", slot="overlay", title="Как подключить Box")
async def box_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("1. Зайдите в Box Developer Console (app.box.com/developers/console) -> Create New App -> \"Custom App\" -> Authentication method: \"Server Authentication (Client Credentials Grant)\".", variant="body"),
        ui.Text("2. На вкладке Configuration скопируйте Client ID и Client Secret.", variant="body"),
        ui.Text("3. Найдите Enterprise ID (там же на Configuration, либо в Admin Console -> Account & Billing).", variant="body"),
        ui.Text("4. На вкладке Authorization отправьте приложение на авторизацию администратору, если оно не авторизовано автоматически -- админ подтверждает его в Admin Console -> Apps -> Custom Apps Manager.", variant="body"),
        ui.Text("5. Вставьте Client ID / Client Secret / Enterprise ID в форму слева и подключитесь.", variant="body"),
    ])