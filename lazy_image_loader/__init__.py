from aiohttp import web
from server import PromptServer

from .lazy_image_loader import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    LazyImageLoader,
    list_input_images,
    open_input_folder,
)

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "LazyImageLoader",
    "list_input_images",
    "open_input_folder",
]


@PromptServer.instance.routes.get("/lazy_image_loader/images")
async def get_lazy_image_list(request):
    return web.json_response(list_input_images())


@PromptServer.instance.routes.post("/lazy_image_loader/open-input")
async def post_lazy_image_open_input(request):
    try:
        path = open_input_folder()
        return web.json_response({"ok": True, "path": path})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)
