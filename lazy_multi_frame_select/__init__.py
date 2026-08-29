from aiohttp import web
from server import PromptServer

from .lazy_multi_frame_select import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    LazyMultiFrameSelect,
    receive_selection,
)

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "LazyMultiFrameSelect",
    "receive_selection",
]


@PromptServer.instance.routes.post("/vsaan212/multi-frame-select")
async def post_multi_frame_select(request):
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid JSON"}, status=400)
    result = receive_selection(body if isinstance(body, dict) else {})
    status = 200 if result.get("ok") else 400
    return web.json_response(result, status=status)
