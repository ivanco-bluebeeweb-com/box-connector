"""Entrypoint for the web-kernel and CLI tools (imperal validate/build).

Sets up sys.path, purges stale module cache, then imports ext/chat and all
handler modules so their decorators register on the same Extension instance
-- same pattern as Splunk Connector's and PagerDuty Connector's main.py.

WHY THE ORDERING AND THE CACHE PURGE MATTER. The handler modules each do
`from app import ext, chat`. If this file is imported from a working
directory that is not on sys.path, or if a previous import left a different
`app` module object in sys.modules, those handler decorators bind to a
*different* Extension instance than the one the platform loads -- so the
platform sees a ChatExtension with zero registered @chat.function entries.
Inserting _EXT_DIR first and popping the local modules before importing
guarantees every decorator lands on the single Extension the server holds.
"""

import os
import sys

_EXT_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXT_DIR not in sys.path:
    sys.path.insert(0, _EXT_DIR)

_LOCAL = (
    "app",
    "schemas",
    "box_client",
    "handlers_collab",
    "handlers_comments_tasks",
    "handlers_connection",
    "handlers_files",
    "handlers_folders",
    "handlers_metadata",
    "handlers_versions",
    "handlers_webhooks",
    "panels",
    "panels_center",
    "panels_settings",
)
for _mod in _LOCAL:
    sys.modules.pop(_mod, None)

from app import ext, chat  # noqa: E402,F401
import handlers_collab  # noqa: E402,F401
import handlers_comments_tasks  # noqa: E402,F401
import handlers_connection  # noqa: E402,F401
import handlers_files  # noqa: E402,F401
import handlers_folders  # noqa: E402,F401
import handlers_metadata  # noqa: E402,F401
import handlers_versions  # noqa: E402,F401
import handlers_webhooks  # noqa: E402,F401
import panels  # noqa: E402,F401
import panels_center  # noqa: E402,F401
import panels_settings  # noqa: E402,F401

extension = ext
