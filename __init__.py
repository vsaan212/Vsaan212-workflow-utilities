__version__ = "1.4.0"
__author__ = "Vsaan212"
__title__ = "Vsaan212 Workflow Utilities"
# custom_nodes/vsaan212_workflow_utilities/__init__.py
import os

WEB_DIRECTORY = "./js"

# --- Robust imports for each submodule (handles legacy filenames too) ---
# Text Split
try:
    from .textsplit.text_split_node import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )
except Exception:
    # fallback for legacy single-file layout
    from .textsplit import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )

# Optional Switch LoRA (autobypass)
try:
    from .optional_switch_lora.optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )
except Exception:
    # fallback for legacy filename
    from .optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )

# Scenario Selector
try:
    from .scenarioselector.scenarioselector import (
        NODE_CLASS_MAPPINGS as SCEN_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
    )
except Exception:
    # fallback for legacy filename (senarioselector.py)
    try:
        from .scenarioselector.senarioselector import (
            NODE_CLASS_MAPPINGS as SCEN_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
        )
    except Exception:
        from .scenarioselector import (
            NODE_CLASS_MAPPINGS as SCEN_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
        )

# Subject Selector
try:
    from .subjectselector.subjectselector import (
        NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
    )
except Exception:
    # fallback for legacy filename (subjectselctor.py)
    try:
        from .subjectselector.subjectselctor import (
            NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
        )
    except Exception:
        from .subjectselector import (
            NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
        )

# Lazy Subject + Scene Automation (v2 combined node)
LazySubjectSceneAutomation = None
try:
    from .lazy_subject_scene_automation.lazy_subject_scene_automation import (
        NODE_CLASS_MAPPINGS as LSSA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LSSA_DISPLAY,
        LazySubjectSceneAutomation as _LazySubjectSceneAutomation,
    )
    LazySubjectSceneAutomation = _LazySubjectSceneAutomation
except Exception:
    try:
        from .lazy_subject_scene_automation import (
            NODE_CLASS_MAPPINGS as LSSA_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as LSSA_DISPLAY,
            LazySubjectSceneAutomation as _LazySubjectSceneAutomation,
        )
        LazySubjectSceneAutomation = _LazySubjectSceneAutomation
    except Exception:
        LSSA_CLASSES = {}
        LSSA_DISPLAY = {}

# Lazy Prompt Saver
from .lazy_prompt_saver import (
    NODE_CLASS_MAPPINGS as LPS_CLASSES,
    NODE_DISPLAY_NAME_MAPPINGS as LPS_DISPLAY,
)

# LazyPrompt (multi-target prompt engineer + vision describe)
try:
    from .lazyprompt import (
        NODE_CLASS_MAPPINGS as LP_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LP_DISPLAY,
    )
except Exception:
    LP_CLASSES = {}
    LP_DISPLAY = {}

# Prompt Garnish (pick one phrase line, append with joiner)
try:
    from .prompt_garnish.prompt_garnish import (
        NODE_CLASS_MAPPINGS as PG_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as PG_DISPLAY,
    )
except Exception:
    try:
        from .prompt_garnish import (
            NODE_CLASS_MAPPINGS as PG_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as PG_DISPLAY,
        )
    except Exception:
        PG_CLASSES = {}
        PG_DISPLAY = {}

# --- API routes for live folder scanning ---
from aiohttp import web
from server import PromptServer
from .subjectselector.subjectselector import ComfyUI_subjectselector
from .scenarioselector.scenarioselector import ComfyUI_ScenarioSelector


@PromptServer.instance.routes.get("/vsaan212/subjects")
async def get_subjects(request):
    ComfyUI_subjectselector.refresh_subjects_list()
    names = sorted(ComfyUI_subjectselector.subjects_relpaths, key=lambda s: s.lower())
    return web.json_response(names)


@PromptServer.instance.routes.get("/vsaan212/scenarios")
async def get_scenarios(request):
    ComfyUI_ScenarioSelector.refresh_scenarios_list()
    names = sorted(ComfyUI_ScenarioSelector.scenarios_relpaths, key=lambda s: s.lower())
    return web.json_response(names)


if LazySubjectSceneAutomation is not None:

    @PromptServer.instance.routes.get("/vsaan212/lazy-subject-scene/subjects")
    async def get_lazy_subjects(request):
        LazySubjectSceneAutomation.refresh_subjects_list()
        names = sorted(
            LazySubjectSceneAutomation.subjects_relpaths, key=lambda s: s.lower()
        )
        return web.json_response(names)

    @PromptServer.instance.routes.get("/vsaan212/lazy-subject-scene/scenarios")
    async def get_lazy_scenarios(request):
        LazySubjectSceneAutomation.refresh_scenarios_list()
        names = sorted(
            LazySubjectSceneAutomation.scenarios_relpaths, key=lambda s: s.lower()
        )
        return web.json_response(names)

    from .lazy_subject_scene_automation.lazy_subject_scene_automation import (
        DEFAULT_SCENARIO_TEMPLATE,
        LAZY_PRESET_WS_EVENT,
    )

    @PromptServer.instance.routes.get("/vsaan212/lazy-subject-scene/presets")
    async def get_lazy_presets(request):
        return web.json_response(LazySubjectSceneAutomation.api_list_presets())

    @PromptServer.instance.routes.get(
        "/vsaan212/lazy-subject-scene/default_scenario_template"
    )
    async def get_lazy_default_scenario_template(request):
        return web.json_response({"scenario_template": DEFAULT_SCENARIO_TEMPLATE})

    @PromptServer.instance.routes.post("/vsaan212/lazy-subject-scene/read_pair")
    async def post_lazy_read_pair(request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        data = LazySubjectSceneAutomation.api_read_pair(
            body.get("subject") or "none",
            body.get("scenario") or "none",
        )
        return web.json_response(data)

    @PromptServer.instance.routes.post("/vsaan212/lazy-subject-scene/load_preset")
    async def post_lazy_load_preset(request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        preset = body.get("preset") or body.get("filename") or ""
        data = LazySubjectSceneAutomation.api_load_preset(str(preset))
        return web.json_response(data)

    @PromptServer.instance.routes.post("/vsaan212/lazy-subject-scene/save_preset")
    async def post_lazy_save_preset(request):
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "invalid JSON"}, status=400)
        result = LazySubjectSceneAutomation.api_save_preset(body)
        if result.get("ok"):
            LazySubjectSceneAutomation.refresh_presets_list()
            PromptServer.instance.send_sync(
                LAZY_PRESET_WS_EVENT,
                {"presets": LazySubjectSceneAutomation.presets_relpaths},
            )
        status = 400 if result.get("error") else 200
        return web.json_response(result, status=status)

# --- Merge exports for ComfyUI ---
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

NODE_CLASS_MAPPINGS.update(TS_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(TS_DISPLAY)

NODE_CLASS_MAPPINGS.update(LORA_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(LORA_DISPLAY)

NODE_CLASS_MAPPINGS.update(SCEN_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(SCEN_DISPLAY)

NODE_CLASS_MAPPINGS.update(SUBJ_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(SUBJ_DISPLAY)

NODE_CLASS_MAPPINGS.update(LSSA_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(LSSA_DISPLAY)

NODE_CLASS_MAPPINGS.update(LPS_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(LPS_DISPLAY)

NODE_CLASS_MAPPINGS.update(LP_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(LP_DISPLAY)

NODE_CLASS_MAPPINGS.update(PG_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(PG_DISPLAY)
