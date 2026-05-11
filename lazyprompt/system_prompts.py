"""Target-model system prompts and router (LazyPrompt).

Default templates load from ``system_prompts.json`` in this folder (next to this file).
Edit that JSON to customize prompts; restart ComfyUI or press **R** (refresh) to reload.
Keys: ``ltx_23``, ``ltx_23_screenplay``, ``wan_22``, ``flux``, ``sdxl``, ``pony``, ``sd15``.
"""

from __future__ import annotations

import json
from pathlib import Path

# Dropdown label for “no template from JSON — empty system unless you use override”
TARGET_NONE_LABEL = "\u23f9 None — empty default system prompt (override optional)"

TARGET_MODELS = [
    TARGET_NONE_LABEL,
    "\U0001f3ac LTX 2.3  — video, cinematic arc + audio",
    "\U0001f3ac Wan 2.2  — video, motion-first cinematic",
    "\U0001f5bc Flux.1   — image, natural language",
    "\U0001f5bc SDXL 1.0 — image, booru tag style",
    "\U0001f5bc Pony XL  — image, booru + score tags",
    "\U0001f5bc SD 1.5   — image, weighted classic",
]

# Default widget selection when adding the node (skip “None”; use LTX)
TARGET_MODEL_DEFAULT = TARGET_MODELS[1]

_JSON_PATH = Path(__file__).with_name("system_prompts.json")
_templates_mtime: float | None = None
_templates_cache: dict[str, str] | None = None


def is_none_target(target_model: str) -> bool:
    t = (target_model or "").strip()
    return t == TARGET_NONE_LABEL or t.startswith("\u23f9 None —")


def _strip_meta_keys(data: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and k.startswith("_"):
            continue
        if isinstance(v, str):
            out[k] = v
    return out


def load_system_prompt_templates() -> dict[str, str]:
    """Load templates from disk; picks up edits after restart or refresh (R)."""
    global _templates_mtime, _templates_cache

    try:
        st = _JSON_PATH.stat()
        mtime = st.st_mtime
    except OSError:
        if _templates_cache is None:
            print(f"[LazyPrompt] Missing system_prompts.json at {_JSON_PATH}")
            _templates_cache = {}
        return _templates_cache or {}

    if _templates_cache is not None and _templates_mtime == mtime:
        return _templates_cache

    try:
        raw = _JSON_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[LazyPrompt] Could not load system_prompts.json: {e}")
        _templates_cache = {}
        _templates_mtime = mtime
        return _templates_cache

    _templates_cache = _strip_meta_keys(data)
    _templates_mtime = mtime
    print(
        f"[LazyPrompt] Loaded {len(_templates_cache)} system prompt template(s) "
        f"from {_JSON_PATH.name}"
    )
    return _templates_cache


def get_system_prompt(target_model: str, screenplay_mode: bool = False) -> str:
    if is_none_target(target_model):
        return ""

    prompts = load_system_prompt_templates()

    if "LTX" in target_model:
        key = "ltx_23_screenplay" if screenplay_mode else "ltx_23"
    elif "Wan" in target_model:
        key = "wan_22"
    elif "Flux" in target_model:
        key = "flux"
    elif "SDXL" in target_model:
        key = "sdxl"
    elif "Pony" in target_model:
        key = "pony"
    elif "SD 1.5" in target_model:
        key = "sd15"
    else:
        key = "flux"

    body = (prompts.get(key) or "").strip()
    if not body:
        body = (prompts.get("flux") or "").strip()
        if body:
            print(f"[LazyPrompt] Template key {key!r} missing or empty; using 'flux' fallback.")
        else:
            print(
                "[LazyPrompt] system_prompts.json has no usable templates — "
                "system message will be empty unless you use the override field."
            )
    return body


def is_video_model(target_model: str) -> bool:
    if is_none_target(target_model):
        return False
    return "LTX" in target_model or "Wan" in target_model


def default_fps_for_target(target_model: str) -> float:
    """
    Default FPS when the Prompt Engineer fps widget is 0 (auto / not overridden).
    Wan → 16, LTX → 25, everything else → 24.
    """
    if "Wan" in target_model:
        return 16.0
    if "LTX" in target_model:
        return 25.0
    return 24.0


def has_audio(target_model: str) -> bool:
    if is_none_target(target_model):
        return False
    return "LTX" in target_model


JSON_PROMPTS_HINT = (
    "Default templates load from lazyprompt/system_prompts.json (restart or R to reload after edits)."
)
