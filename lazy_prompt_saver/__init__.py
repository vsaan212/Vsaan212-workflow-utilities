from .lazy_prompt_saver import LazyPromptSaver, StorageManager

from aiohttp import web
from server import PromptServer

NODE_CLASS_MAPPINGS = {
    "LazyPromptSaver": LazyPromptSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyPromptSaver": "Lazy Prompt Saver",
}


@PromptServer.instance.routes.get("/lazy_prompt_saver/prompts")
async def get_prompts(request):
    prompts = StorageManager.load_prompts()
    return web.json_response(prompts)


@PromptServer.instance.routes.post("/lazy_prompt_saver/save")
async def save_prompt(request):
    data = await request.json()
    name = data.get("name", "").strip()
    text = data.get("text", "")
    if not name:
        return web.json_response({"error": "Name is required"}, status=400)
    StorageManager.save_prompt(name, text)
    names = StorageManager.get_prompt_names()
    return web.json_response({"names": names})


@PromptServer.instance.routes.post("/lazy_prompt_saver/delete")
async def delete_prompt(request):
    data = await request.json()
    name = data.get("name", "").strip()
    if not name:
        return web.json_response({"error": "Name is required"}, status=400)
    StorageManager.delete_prompt(name)
    names = StorageManager.get_prompt_names()
    return web.json_response({"names": names})


