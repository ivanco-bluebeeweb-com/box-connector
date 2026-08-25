"""Box Connector entrypoint."""
from __future__ import annotations

import handlers_collab  # noqa: F401
import handlers_comments_tasks  # noqa: F401
import handlers_connection  # noqa: F401
import handlers_files  # noqa: F401
import handlers_folders  # noqa: F401
import handlers_metadata  # noqa: F401
import handlers_versions  # noqa: F401
import handlers_webhooks  # noqa: F401
import panels  # noqa: F401
import panels_center  # noqa: F401
import panels_settings  # noqa: F401
from app import ext

extension = ext
