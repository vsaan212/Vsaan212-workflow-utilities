"""DEBUG logs for vsaan212 nodes. Visible when Comfy logging is set to DEBUG / detail."""
from __future__ import annotations

import logging

logger = logging.getLogger("vsaan212")


def debug(node: str, message: str) -> None:
    logger.debug("%s %s", node, message)
