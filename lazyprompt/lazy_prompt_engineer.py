from __future__ import annotations

import re
import os
import io
import json
import base64
import urllib.request
import urllib.error

import numpy as np
from PIL import Image as PILImage

# ── HuggingFace housekeeping ─────────────────────────────────────────────────
# Only disable telemetry at import time — safe, does not block downloads.
# Offline/online state is controlled per-run via the offline_mode toggle.
# Do NOT set TRANSFORMERS_OFFLINE / HF_HUB_OFFLINE here — doing so at module
# import time blocks downloads even when offline_mode is OFF.
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
# ─────────────────────────────────────────────────────────────────────────────

import torch
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer

from .environment_presets import ENVIRONMENT_PRESETS
from .message_builder import (
    build_prompt_augmentation,
    compose_user_scene_input,
    split_positive_negative_block,
)
from .system_prompts import (
    SKILLS_HINT,
    apply_user_prompt_injection,
    get_default_target_model,
    get_system_prompt,
    get_target_model_choices,
    is_none_target,
    is_tag_style_model,
    is_video_model,
)
from ..workflow_modes import (
    parse_selector_tagged,
    resolve_mode_from_selector,
)

import folder_paths

# Closed Prompt-side LoRA markers (LLM / [Prompt] output). Distinct from SAS file
# section tags like [LoraHighA]. Parsed after the LLM (or bypass), then stripped.
_LORA_PROMPT_BLOCK_RE = re.compile(
    r"\[(LoraH|LoraL)\](.*?)\[/\1\]",
    re.IGNORECASE | re.DOTALL,
)


def parse_and_strip_prompt_loras(text: str) -> tuple[str, list[str], list[str]]:
    """
    Pull [LoraH]path[/LoraH] / [LoraL]path[/LoraL] out of Prompt text.

    Returns (clean_text, high_paths, low_paths). Empty / bypass paths are omitted
    from the load lists but still removed from the text.
    """
    if not text:
        return "", [], []

    high: list[str] = []
    low: list[str] = []
    for match in _LORA_PROMPT_BLOCK_RE.finditer(text):
        kind = (match.group(1) or "").lower()
        path = (match.group(2) or "").strip().strip('"').strip("'")
        if not path or path.lower() == "bypass":
            continue
        if kind == "lorah":
            high.append(path)
        else:
            low.append(path)

    clean = _LORA_PROMPT_BLOCK_RE.sub("", text)
    clean = re.sub(r"[ \t]+\n", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean, high, low


def _resolve_prompt_lora_name(cmd: str) -> str:
    path = (cmd or "").strip().strip('"').strip("'")
    if not path:
        return ""
    if os.path.exists(path):
        from comfy import model_management

        lora_dir = os.path.dirname(os.path.abspath(path))
        model_management.lora_paths.add(lora_dir)
        return os.path.basename(path)
    return path


def _apply_prompt_lora_paths(model, clip, paths: list[str], label: str):
    """Apply LoRA paths to a MODEL+CLIP pair (stock LoraLoader). No-op if empty."""
    if not paths:
        return model, clip
    if model is None:
        print(
            f"[LazyPrompt] {label}: {len(paths)} path(s) in Prompt but model not wired — skipped."
        )
        return model, clip
    if clip is None:
        print(f"[LazyPrompt] {label}: CLIP not wired — skipped load.")
        return model, clip

    from nodes import LoraLoader

    loader = LoraLoader()
    for path in paths:
        lora_name = _resolve_prompt_lora_name(path)
        if not lora_name or lora_name.lower() == "bypass":
            continue
        print(f"[LazyPrompt] {label}: loading {lora_name}")
        model, clip = loader.load_lora(model, clip, lora_name, 1.0, 1.0)
    return model, clip


def _unique_lora_paths(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for path in group:
            key = path.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(path)
    return out


def apply_prompt_lora_blocks(
    prompt_text: str,
    model_high=None,
    clip_high=None,
    model_low=None,
    clip_low=None,
    also_collect_from: str = "",
):
    """
    Strip Prompt LoRA blocks and load them onto high/low stacks (like SAS slots).

    LoraH → model_high / clip_high; LoraL → model_low (clip_low, or clip_high if
    low CLIP is unwired). Strengths default to 1.0.

    Paths are taken from the final Prompt text and optionally from
    ``also_collect_from`` (e.g. scenario ``[Prompt]`` / override) so authored
    tags still load if the LLM rewrites the scene without echoing them.
    Only ``prompt_text`` is stripped for the string outputs.
    """
    clean, high_out, low_out = parse_and_strip_prompt_loras(prompt_text or "")
    high_in: list[str] = []
    low_in: list[str] = []
    extra = (also_collect_from or "").strip()
    if extra and extra != (prompt_text or ""):
        _, high_in, low_in = parse_and_strip_prompt_loras(extra)

    high_paths = _unique_lora_paths(high_in, high_out)
    low_paths = _unique_lora_paths(low_in, low_out)
    if high_paths or low_paths:
        print(
            f"[LazyPrompt] Prompt LoRA blocks: {len(high_paths)} LoraH, "
            f"{len(low_paths)} LoraL — stripped before model handoff."
        )

    model_h, clip_h = _apply_prompt_lora_paths(
        model_high, clip_high, high_paths, "LoraH"
    )
    if model_low is not None:
        clip_for_low = clip_low if clip_low is not None else clip_high
        model_l, clip_l_applied = _apply_prompt_lora_paths(
            model_low, clip_for_low, low_paths, "LoraL"
        )
        clip_l = clip_l_applied if clip_low is not None else None
    else:
        if low_paths:
            print(
                "[LazyPrompt] LoraL path(s) in Prompt but model_low not wired — skipped."
            )
        model_l, clip_l = None, None

    return clean, model_h, model_l, clip_h, clip_l


def _strip_input_prefix(path: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    low = p.lower()
    if low.startswith("input/"):
        p = p[6:]
    return p.strip().lstrip("/")


def _load_image_tensor_from_input(rel_path: str):
    """Load IMAGE tensor from Comfy input/ path, or None."""
    rel = _strip_input_prefix(rel_path)
    if not rel:
        return None
    try:
        full = folder_paths.get_annotated_filepath(rel)
    except Exception:
        full = os.path.join(folder_paths.get_input_directory(), rel)
    if not full or not os.path.isfile(full):
        return None
    try:
        img = PILImage.open(full)
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img).convert("RGB")
        arr = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(arr)[None,]
    except Exception:
        return None


def _load_audio_dict_from_input(rel_path: str):
    """Load Comfy AUDIO dict from input/ without torchcodec when possible."""
    rel = _strip_input_prefix(rel_path)
    if not rel:
        return None
    try:
        full = folder_paths.get_annotated_filepath(rel)
    except Exception:
        full = os.path.join(folder_paths.get_input_directory(), rel)
    if not full or not os.path.isfile(full):
        return None

    def _to_dict(waveform, sample_rate: int):
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        if waveform.dim() == 2:
            waveform = waveform.unsqueeze(0)
        return {"waveform": waveform.contiguous().float(), "sample_rate": int(sample_rate)}

    try:
        import soundfile as sf

        data, sr = sf.read(full, dtype="float32", always_2d=True)
        return _to_dict(torch.from_numpy(data.T.copy()), sr)
    except Exception:
        pass
    try:
        import wave

        with wave.open(full, "rb") as wf:
            sr = wf.getframerate()
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())
        if sw == 2:
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 4:
            arr = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sw == 1:
            arr = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            return None
        if n_ch > 1:
            arr = arr.reshape(-1, n_ch).T
        else:
            arr = arr.reshape(1, -1)
        return _to_dict(torch.from_numpy(arr.copy()), sr)
    except Exception:
        pass
    try:
        import torchaudio

        try:
            waveform, sr = torchaudio.load(full, backend="soundfile")
        except TypeError:
            try:
                torchaudio.set_audio_backend("soundfile")
            except Exception:
                pass
            waveform, sr = torchaudio.load(full)
        return _to_dict(waveform, sr)
    except Exception:
        return None


def _gate_media_for_mode(
    mode: str | None,
    first_frame=None,
    last_frame=None,
    refs=None,
    audio=None,
    *,
    sas_override: bool = False,
):
    """Return gated (first, last, refs[5], audio) for mode. Empty mode → pass through."""
    refs = list(refs or [None] * 5)
    while len(refs) < 5:
        refs.append(None)
    refs = refs[:5]

    if sas_override or mode:
        # When mode known (or SAS active with resolved mode), apply hard gates.
        m = mode
        if not m:
            # SAS blob with paths but no Workflow: infer
            if any(r is not None for r in refs) or audio is not None:
                m = "R2V"
            elif first_frame is not None and last_frame is not None:
                m = "FL2V"
            elif first_frame is not None:
                m = "I2V"
            else:
                m = "T2V"
        if m == "T2V":
            return None, None, [None] * 5, None, m
        if m == "I2V":
            return first_frame, None, [None] * 5, None, m
        if m == "FL2V":
            return first_frame, last_frame, [None] * 5, None, m
        if m == "R2V":
            return None, None, refs, audio, m
    return first_frame, last_frame, refs, audio, mode


def _comfy_image_to_jpeg_data_url(image_tensor, max_side: int = 768) -> str:
    """
    ComfyUI IMAGE (B,H,W,C) → data:image/jpeg;base64,... for LM Studio OpenAI-compatible vision API.
    Same pattern as comfyui-lmstudio-image-to-text-node legacy HTTP mode.
    """
    frame = image_tensor[0] if getattr(image_tensor, "ndim", 0) == 4 else image_tensor
    arr = (frame.detach().cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
    pil = PILImage.fromarray(arr, mode="RGB")
    w, h = pil.size
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        pil = pil.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=85, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


# ── Negative prompt builder ───────────────────────────────────────────────────
# Builds a scene-aware negative prompt without a second LLM call.
# Base quality terms are always included; scene-specific terms are added
# by scanning the generated prompt for relevant content.

_NEG_BASE = (
    "blurry, out of focus, low quality, worst quality, jpeg artifacts, "
    "static, no motion, frozen, duplicate, watermark, text, signature, "
    "poorly drawn, bad anatomy, deformed, disfigured, extra limbs, "
    "missing limbs, floating limbs, disconnected body parts, "
    "overexposed, underexposed, grainy, noise"
)

_NEG_INDOOR   = "harsh outdoor lighting, direct sunlight"
_NEG_OUTDOOR  = "studio background, indoor lighting"
_NEG_EXPLICIT = "censored, mosaic, pixelated, black bar, blurred genitals"
_NEG_PORTRAIT = "wide angle distortion, fish eye, full body shot"
_NEG_WIDE     = "close-up, portrait crop, tight frame"
_NEG_NIGHT    = "overexposed, bright daylight, blown highlights"
_NEG_DAY      = "underexposed, dark shadows, black crush"
_NEG_MULTI    = "merged bodies, fused figures, incorrect number of people"

def _build_negative_prompt(result: str, user_input: str) -> str:
    combined = (result + " " + user_input).lower()
    extras = []

    if any(w in combined for w in ["indoor", "room", "interior", "bedroom", "kitchen", "office"]):
        extras.append(_NEG_OUTDOOR)
    elif any(w in combined for w in ["outdoor", "street", "beach", "forest", "park", "exterior"]):
        extras.append(_NEG_INDOOR)

    if any(w in combined for w in ["pussy", "cock", "penis", "vagina", "nude", "naked", "explicit", "nipple", "breast"]):
        extras.append(_NEG_EXPLICIT)

    if any(w in combined for w in ["close-up", "close up", "portrait", "face shot", "headshot"]):
        extras.append(_NEG_PORTRAIT)
    elif any(w in combined for w in ["wide shot", "wide angle", "aerial", "bird's-eye", "establishing"]):
        extras.append(_NEG_WIDE)

    if any(w in combined for w in ["night", "dark", "moonlight", "dimly lit", "candlelight"]):
        extras.append(_NEG_NIGHT)
    elif any(w in combined for w in ["daylight", "sunny", "golden hour", "bright", "midday"]):
        extras.append(_NEG_DAY)

    if any(w in combined for w in ["two women", "two men", "two people", "both", "together", "couple", "they "]):
        extras.append(_NEG_MULTI)

    parts = [_NEG_BASE] + extras
    return ", ".join(parts)


_GENERIC_IMAGE_NEG = (
    "worst quality, bad quality, blurry, low resolution, deformed, bad anatomy, "
    "extra limbs, missing fingers, watermark, text, ugly, duplicate, out of frame"
)

# Upper bound for the max_output_tokens widget (HF max_new_tokens / LM Studio max_tokens).
_ABS_MAX_OUTPUT_TOKENS = 16000


class LazyPromptEngineer:
    @classmethod
    def INPUT_TYPES(s):
        env_keys = list(ENVIRONMENT_PRESETS.keys())
        target_choices = get_target_model_choices()
        return {
            "required": {
                "bypass": ("BOOLEAN", {"default": False, "tooltip": "When ON, skips the LLM entirely and sends your text straight through. Use for manual prompts or testing."}),
                "user_input": ("STRING", {
                    "multiline": True,
                    "default": "a woman walks through a rain-soaked city street at night",
                    "tooltip": "Prompt to be enhanced — short idea, sentence, or numbered steps. The LLM expands it for the selected skill.",
                }),
                "target_model": (
                    target_choices,
                    {
                        "default": get_default_target_model(),
                        "tooltip": (
                            "Skill / output format for the LLM system prompt. "
                            '"None" = no Model_Skills template (empty system unless override). '
                            + SKILLS_HINT
                        ),
                    },
                ),
                "environment": (
                    env_keys,
                    {
                        "default": "None — LLM decides",
                        "tooltip": "Injects location, lighting, and (for video) sound. Random uses env_seed.",
                    },
                ),
                "creativity": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "number",
                    "tooltip": "Sampling temperature (0.1–1.0, step 0.1) for local HF models and LM Studio. Values above 1.0 are not supported by LM Studio.",
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "LLM seed. -1 = random each run.",
                }),
                "keep_model_loaded": ("BOOLEAN", {"default": False, "tooltip": "Keep the local HF model in VRAM between runs. Off frees VRAM after each run."}),
                "offline_mode": ("BOOLEAN", {"default": False, "tooltip": "ON = no HuggingFace network; local cache / paths only."}),
                "video_length": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.25,
                    "max": 300.0,
                    "step": 0.25,
                    "display": "number",
                    "tooltip": "Video duration in seconds. Injected into the LLM prompt for video skills. Image skills ignore this.",
                }),
                "env_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "Seed when environment is Random. 0 = different pick each run.",
                }),
                "model": ([
                    "8B - NeuralDaredevil (High Quality)",
                    "3B - Llama-3.2 Abliterated (Low VRAM)",
                    "LM Studio (API)",
                    "TextGenerate (CLIP)",
                ], {
                    "default": "LM Studio (API)",
                    "tooltip": (
                        "Backend: local HF checkpoints, LM Studio REST API, or Comfy core "
                        "TextGenerate via a wired CLIP/LLM (Qwen etc.). "
                        "TextGenerate requires the optional clip input."
                    ),
                }),
                "local_path_8b": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "NeuralDaredevil 8B snapshot folder",
                    "tooltip": "Optional local snapshot path for the 8B model.",
                }),
                "local_path_3b": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Llama 3.2 3B snapshot folder",
                    "tooltip": "Optional local snapshot path for the 3B model.",
                }),
                "lm_studio_model": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Model id as shown in LM Studio",
                    "tooltip": "Required when model is LM Studio (API). LM Studio 0.4+ uses /api/v1/chat; older versions fall back to /v1/chat/completions.",
                }),
                "lm_studio_ttl": ("INT", {
                    "default": 5,
                    "min": 0,
                    "max": 3600,
                    "step": 1,
                    "display": "number",
                    "tooltip": "LM Studio JIT unload: when > 0, unloads the model immediately after each run via /api/v1/models/unload (v1 chat). On OpenAI fallback only, also sends idle TTL in the request body. 0 = leave loaded.",
                }),
                "max_output_tokens": ("INT", {
                    "default": 900,
                    "min": 96,
                    "max": _ABS_MAX_OUTPUT_TOKENS,
                    "step": 16,
                    "display": "number",
                    "tooltip": (
                        "Hard cap on completion length (HF max_new_tokens / LM Studio max_tokens / "
                        "TextGenerate max_length). "
                        "The pacing hint asks the model for ~one-third of this many tokens by default — "
                        "raise both together for longer prompts (e.g. 1500 max → ~500 target)."
                    ),
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Leave empty = Model_Skills template for target_model",
                    "tooltip": (
                        "Optional full system override. Empty = selected skill's Model_Skills/*.md prompt. "
                        "Does not merge with the MD body. "
                        "When target is None and this field has text, only that text is used as system prompt and the "
                        "user message is scene + idea only (no auto augmentation). "
                        + SKILLS_HINT
                    ),
                }),
                "textgenerate_thinking": ("BOOLEAN", {
                    "default": False,
                    "tooltip": (
                        "TextGenerate (CLIP) only: enable thinking mode when the wired LLM supports it."
                    ),
                }),
            },
            "optional": {
                "clip": ("CLIP", {
                    "tooltip": (
                        "Required for TextGenerate (CLIP) backend. Wire CLIPLoader with an LLM-capable "
                        "encoder (e.g. Qwen, type minimax / qwen). Plain SD CLIP will fail — needs .generate()."
                    ),
                }),
                "scene_context": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Wire LazyPrompt Vision Describe output here (optional)",
                    "tooltip": "Authoritative scene/subject text from the vision node or manual paste.",
                }),
                "lora_triggers": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Triggers prepended to model output",
                    "tooltip": "Injected so the model places these words at the very start of the output.",
                }),
                "character": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Wire subject_description from Lazy-subject-and-scene-automation",
                    "tooltip": (
                        "Subject / character description — always prepended to the LLM user message "
                        "(including minimal mode and when prompt_override_input is set). "
                        "Wire from Lazy-subject-and-scene-automation subject_description."
                    ),
                }),
                "first_frame": ("IMAGE", {
                    "tooltip": (
                        "Image2video First frame. Vision for LM Studio or TextGenerate (CLIP) when gated on. "
                        "Also accepted via legacy `image` input."
                    ),
                }),
                "image": ("IMAGE", {
                    "tooltip": (
                        "Legacy alias for Image2video First frame. Prefer first_frame."
                    ),
                }),
                "last_frame": ("IMAGE", {
                    "tooltip": "Image2video Last frame (FL2V).",
                }),
                "reference_image_1": ("IMAGE", {"tooltip": "Reference Image 1 (R2V)."}),
                "reference_image_2": ("IMAGE", {"tooltip": "Reference Image 2 (R2V)."}),
                "reference_image_3": ("IMAGE", {"tooltip": "Reference Image 3 (R2V)."}),
                "reference_image_4": ("IMAGE", {"tooltip": "Reference Image 4 (R2V)."}),
                "reference_image_5": ("IMAGE", {"tooltip": "Reference Image 5 (R2V)."}),
                "reference_audio": ("AUDIO", {
                    "tooltip": "Reference audio passthrough (R2V). Switchable by global selector.",
                }),
                "global_selector_input": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": False,
                    "tooltip": "From Lazy Global Selector (T2V/I2V/FL2V/R2V). Gates image/audio sockets.",
                }),
                "SAS_automation_selector_input": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": (
                        "From Lazy-subject-and-scene-automation selector. Mode tags always apply. "
                        "Direct image/audio sockets are ignored only when the blob includes "
                        "ReferenceImage/AudioReference paths (disk load). Workflow-only blobs "
                        "keep wired Lazy Image Loader frames."
                    ),
                }),
                "prompt_override_input": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": (
                        "When connected/non-empty, replaces user_input for the LLM request "
                        "(LM Studio API and local HF). Wire from Lazy-subject-and-scene-automation prompt_override."
                    ),
                }),
                "user_instructions": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": (
                        "Optional temporary instructions. When non-empty, injected between "
                        "***UserPrompt*** / ***UserPromptEnd*** in the system prompt. "
                        "Empty = block omitted (nothing passed)."
                    ),
                }),
                "model_high": ("MODEL", {
                    "tooltip": (
                        "Optional high stack (after SAS / checkpoint). Prompt [LoraH]path[/LoraH] "
                        "blocks load here after the LLM, then are stripped from PROMPT."
                    ),
                }),
                "clip_high": ("CLIP", {
                    "tooltip": (
                        "CLIP paired with model_high for Prompt [LoraH] loads. "
                        "Separate from the TextGenerate clip input."
                    ),
                }),
                "model_low": ("MODEL", {
                    "tooltip": (
                        "Optional low stack. Prompt [LoraL]path[/LoraL] blocks load here "
                        "after the LLM (Wan-style dual noise / low branch)."
                    ),
                }),
                "clip_low": ("CLIP", {
                    "tooltip": (
                        "CLIP paired with model_low for Prompt [LoraL] loads. "
                        "If unwired, LoraL still patches model_low using clip_high."
                    ),
                }),
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "IMAGE",
        "AUDIO",
        "MODEL",
        "MODEL",
        "CLIP",
        "CLIP",
    )
    RETURN_NAMES = (
        "PROMPT",
        "PREVIEW",
        "NEG_PROMPT",
        "selector_Out",
        "first_frame",
        "last_frame",
        "reference_image_1",
        "reference_image_2",
        "reference_image_3",
        "reference_image_4",
        "reference_image_5",
        "reference_audio",
        "model_high",
        "model_low",
        "clip_high",
        "clip_low",
    )
    FUNCTION = "generate"
    CATEGORY = "vsaan212/LazyPrompt"

    # ── Model registry ───────────────────────────────────────────────────────
    # Maps dropdown label → HuggingFace model ID for auto-download
    MODELS = {
        "8B - NeuralDaredevil (High Quality)": "mlabonne/NeuralDaredevil-8B-abliterated",
        "3B - Llama-3.2 Abliterated (Low VRAM)": "huihui-ai/Llama-3.2-3B-Instruct-abliterated",
    }

    # Default target templates: lazyprompt/Model_Skills/*.md (editable)

    _PREAMBLE_RE = re.compile(
        r"^(Sure!?|Certainly!?|Absolutely!?|Of course!?|Here(?:'s| is).*?:|Great!?)[^\n]*\n?",
        re.IGNORECASE,
    )
    # Role-bleed: strips trailing "assistant", "user", "<|...|>" fragments that
    # NeuralDaredevil / Llama-chat templates leave as plain text at end of output.
    _ROLE_BLEED_RE = re.compile(
        r"\s*(assistant|user|system|<\|[^|>]*\|>)\s*$",
        re.IGNORECASE,
    )

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.loaded_model_key = None  # tracks which model is currently in VRAM

    def load_model(self, model_key: str, offline_mode: bool, local_path: str):
        # ── Switch detection ─────────────────────────────────────────────────
        # If a different model is requested, unload the current one first
        if self.model is not None and self.loaded_model_key != model_key:
            print(f"[LazyPrompt] Model switch detected: {self.loaded_model_key} → {model_key}")
            self.unload_model()

        if self.model is not None:
            return  # already loaded and correct model

        # ── Offline / online mode ────────────────────────────────────────────
        if offline_mode:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
            print("[LazyPrompt] Offline mode ON — no network calls will be made.")
        else:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
            os.environ.pop("HF_DATASETS_OFFLINE", None)
            os.environ.pop("HF_HUB_OFFLINE", None)
            print("[LazyPrompt] Offline mode OFF — will download if needed.")

        # ── Resolve model source ─────────────────────────────────────────────
        # Priority: local_path field → HF cache (offline) → auto-download (online)
        hf_model_id = self.MODELS[model_key]

        if local_path.strip():
            # User has pointed us at a specific folder — use it directly
            model_source = local_path.strip()
            print(f"[LazyPrompt] Using local path: {model_source}")
        elif offline_mode:
            # No local path but offline — fall back to HF cache on disk
            model_source = hf_model_id
            print(f"[LazyPrompt] Using HF cache for: {hf_model_id}")
        else:
            # Online mode — auto-download from HuggingFace if not cached
            print(f"[LazyPrompt] Auto-downloading if needed: {hf_model_id}")
            try:
                from huggingface_hub import snapshot_download
                model_source = snapshot_download(hf_model_id)
                print(f"[LazyPrompt] Model ready at: {model_source}")
            except Exception as e:
                print(f"[LazyPrompt] snapshot_download failed, falling back to model ID: {e}")
                model_source = hf_model_id

        print(f"[LazyPrompt] Loading: {model_key}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_source,
            local_files_only=offline_mode,
        )

        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(
            model_source,
            device_map="auto",
            torch_dtype=dtype,
            trust_remote_code=True,
            local_files_only=offline_mode,
        )

        self.model.config.use_cache = True
        self.model.eval()
        self.loaded_model_key = model_key
        print(f"[LazyPrompt] Loaded: {model_key}")

    def unload_model(self):
        if self.model is not None:
            try:
                self.model.to("cpu")
            except Exception as e:
                print(f"[LazyPrompt] Warning: could not move model to CPU: {e}")

        try:
            del self.model
        except Exception as e:
            print(f"[LazyPrompt] Warning: could not delete model: {e}")

        try:
            del self.tokenizer
        except Exception as e:
            print(f"[LazyPrompt] Warning: could not delete tokenizer: {e}")

        self.model = None
        self.tokenizer = None
        self.loaded_model_key = None

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        print("[LazyPrompt] Model unloaded.")

    @staticmethod
    def _clean_output(text: str) -> str:
        """
        Strip common LLM preamble, role-token bleed, and compliance checklists.

        NeuralDaredevil uses plain-text role labels (e.g. 'assistant') rather
        than dedicated special tokens, so skip_special_tokens=True doesn't catch
        them. We handle four cases:
          1. Preamble at the start  ("Sure!", "Here's your prompt:", etc.)
          2. Role word at the end   ("...and water.assistant")
          3. Role word mid-text     (multiple generations concatenated with role labels)
          4. Compliance checklist   ("(Exactly 4 actions...)(Pacing strict)..." etc.)
        """
        text = text.strip()

        # 1. Strip leading preamble
        text = LazyPromptEngineer._PREAMBLE_RE.sub("", text)

        # 2. Strip trailing role bleed  ("...darkness and water.assistant")
        text = LazyPromptEngineer._ROLE_BLEED_RE.sub("", text)

        # 3. Strip inline role injections between sentences
        #    e.g. "...fish gliding past.assistant\n\nA couple embracing..."
        text = re.sub(
            r"\.(assistant|user|system|<\|[^|>]*\|>)\s*\n",
            ".\n",
            text,
            flags=re.IGNORECASE,
        )

        # 4. Strip trailing compliance content — model sometimes appends:
        #    - A "Note:" explanation block after the scene ends
        #    - A single parenthesised summary line: "(5 distinct actions within 20 seconds)"
        #    - Consecutive bracketed phrases: "(Exactly 4 actions)(Pacing strict)..."
        #    - Self-justification paragraph: "1026 tokens, 15-second scene..." etc.
        #    - Fake conversation loop: "Please let me know...", "Let me revise...", "Confirmed." etc.
        #    Order matters: strip Note: first so it doesn't shield bracket lines above it.
        text = re.sub(
            r"\s*\n+Note:.*$",
            "",
            text,
            flags=re.DOTALL,
        ).strip()

        # Strip everything AFTER the AMBIENT tag if one still appears (legacy cleanup)
        # — the tag itself stays, but anything the model writes beyond it is garbage.
        ambient_match = re.search(r"\[AMBIENT:[^\]]*\]", text, flags=re.IGNORECASE)
        if ambient_match:
            text = text[:ambient_match.end()].strip()

        # Strip trailing (Lora: ...) tags the model echoes from the LoRA instruction
        text = re.sub(r"\s*\(Lora:[^)]*\)\s*$", "", text, flags=re.IGNORECASE).strip()

        # Strip trailing (Note: ...) blocks and everything after — use DOTALL so it
        # catches multi-line notes and the bracket spam that follows them.
        text = re.sub(r"\s*\(Note:.*$", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

        # Strip orphaned closing bracket spam: ) ) ) ) ) ...
        text = re.sub(r"[\s)]{3,}$", "", text).strip()

        # Catch the fake conversation / self-eval patterns
        text = re.sub(
            r"\s*\n+\d+\s+tokens[\s,].*$",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()
        text = re.sub(
            r"\s*\n+(Please let me know|Let me revise|No further revision|Confirmed\.|"
            r"Written to meet|The scene is now over|The output ends|The task is|The task was|"
            r"The goal was|Nothing more|No continuation|No additional|The response does not|"
            r"It does not continue|It ceases when|Any such statement|"
            r"Output length:|Action count:|Total time:|Last character:|I avoided|I wrote|"
            r"I adhered|I hope this|Thank you for your|Please confirm|I submitted|"
            r"I can revise|feel free to instruct).*$",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()

        # Strip model loop/panic — hits token ceiling and repeats stop phrases.
        # NOTE: no \n requirement — panic starts inline after last sentence.
        text = re.sub(
            r"\s*(Ended\.\s*\d+\s*actions|"
            r"\d+\s+actions[\.,]\s*\d+\s+tokens|"
            r"\d+\s+tokens[\.,]\s*Done|"
            r"Done\.\s+\d+\s+seconds|"
            r"Finished\.\s+\d+|"
            r"The end\.\s+\d+\s+seconds|"
            r"Fading to black\.\s+The end|"
            r"The model stops|The output ends here|The scene ends here|"
            r"It\'s complete now|All done\.|Stop now\.|"
            r"End of prompt|End of output|No more to add|Nothing to revise|"
            r"The work is (?:done|finished|complete)|The prompt is (?:done|finished|complete)|"
            r"No further writing|No more writing|Stop\.\s+Finish|Finished\.\s+Complete|"
            r"The scene is complete|The scene is over|Complete\.\s+Finished|"
            r"Done\.\s+No more|BorderSide:).*$",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        ).strip()

        # Strip filler character spam — e.g. "a a a a a a a a a a" repeated tokens
        text = re.sub(r"(\s*\b(\w)\b\s*){10,}", " ", text).strip()

        # Strip token+action count combos inline or at end — e.g. "(840 tokens, 7 actions)"
        text = re.sub(r"\s*\(\d+\s+tokens?[^)]*\)", "", text, flags=re.IGNORECASE).strip()

        # Strip compliance checklist spam — 2+ consecutive parens after last sentence
        text = re.sub(r"\s*(\([^)]{5,120}\)\s*){2,}$", "", text, flags=re.DOTALL).strip()

        # Strip single trailing compliance paren with known instruction keywords
        text = re.sub(
            r"\s*\([^)]{0,200}(no setup|no resolution|action count|actions adhered|"
            r"token count|pacing|dialogue integrated|character age|inline prose|"
            r"no padding|no extraneous|exactly \d+ action|hard stop|BorderSide)[^)]{0,200}\)\s*$",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

        # Strip leaked pacing instruction echoes — e.g. "(Exact timing: 0-4 sec: Soaring...)"
        text = re.sub(r"\(Exact timing:.*?\)", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

        # Strip token/word count lines — e.g. "Token count: 256"
        text = re.sub(r"\s*\n*(token|word)\s+count\s*:\s*\d+.*$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

        # 5. Strip leaked internal pacing/time tags the model sometimes echoes back
        text = re.sub(r"\[TIME LIMIT[^\]]*\]", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\[PACING[^\]]*\]",     "", text, flags=re.IGNORECASE).strip()

        # Strip leaked timestamp — e.g. "(42221149502953 seconds)" or "(0:00 - 4:00)"
        text = re.sub(r"\s*\(\d+\s+seconds?\)\s*$", "", text).strip()
        text = re.sub(r"\s*\(\d+:\d+\s*[-–]\s*\d+:\d+\)\s*", " ", text).strip()

        # Strip inline action-time annotations — e.g. "(The action takes up roughly 5 seconds)"
        text = re.sub(r"\(The action takes up roughly[^\)]*\)", " ", text, flags=re.IGNORECASE).strip()

        # 6. Strip screenplay-style bracketed camera directions
        #    e.g. (DOWN 10 degrees), (Pull back 5), (HOLD), (Fade to black), (Zoom in to...)
        text = re.sub(r"\((?:DOWN|UP|PULL|PUSH|ZOOM|HOLD|FADE|PAN|TILT|TRUCK|DOLLY|AMBIENT)[^\)]{0,80}\)", "", text, flags=re.IGNORECASE).strip()

        # 7. Strip any [AMBIENT: ...] tags if the model still writes one (legacy fallback)
        #    — convert it to clean prose by stripping the tag wrapper
        text = re.sub(r"\[AMBIENT:\s*([^\]]*)\]", r"\1", text, flags=re.IGNORECASE).strip()

        # Clean up any double blank lines left by removals
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return text.strip()

    @staticmethod
    def _finalize_output(target_model: str, result: str, user_input: str) -> tuple:
        """Strip POSITIVE/NEGATIVE blocks for tag-style image targets; else scene-aware video neg."""
        if is_tag_style_model(target_model):
            pos, neg_img = split_positive_negative_block(result)
            neg = neg_img.strip() if neg_img.strip() else _GENERIC_IMAGE_NEG
            return pos, neg
        if not is_video_model(target_model):
            return result, _GENERIC_IMAGE_NEG
        return result, _build_negative_prompt(result, user_input)

    def _build_stop_token_ids(self) -> list:
        """
        Build the complete list of token IDs that should hard-stop generation.

        NeuralDaredevil (and most Llama-based chat models) use plain-text role
        delimiters like 'assistant', '<|eot_id|>', '<|end_of_turn|>' etc.
        Because these are encoded as normal text tokens — not registered special
        tokens — skip_special_tokens=True never removes them.

        The fix: tokenise every known delimiter string ourselves, extract the
        first token ID of each (the one the model will emit first when it starts
        writing the delimiter), and pass the full list as eos_token_id so
        generation hard-stops the moment any delimiter begins.
        """
        # Known role / turn delimiters used by Llama-3, Mistral, NeuralDaredevil,
        # ChatML, and Gemma chat templates.
        delimiter_strings = [
            "assistant",
            "user",
            "system",
            "<|eot_id|>",
            "<|end_of_turn|>",
            "<|im_end|>",
            "<end_of_turn>",
            "[/INST]",
            "### Human",
            "### Assistant",
        ]

        stop_ids = [self.tokenizer.eos_token_id]

        for s in delimiter_strings:
            # encode without adding BOS so we get just the raw token(s)
            ids = self.tokenizer.encode(s, add_special_tokens=False)
            if ids:
                # Only need the FIRST token — that's what triggers the stop
                stop_ids.append(ids[0])

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for tid in stop_ids:
            if tid is not None and tid not in seen:
                seen.add(tid)
                unique.append(tid)

        print(f"[LazyPrompt] Stop token IDs: {unique}")
        return unique

    # Stop sequences for LM Studio OpenAI-compatible fallback (/v1/chat/completions)
    LM_STUDIO_STOP = [
        "assistant", "user", "system",
        "<|eot_id|>", "<|end_of_turn|>", "<|im_end|>",
        "<end_of_turn>", "[/INST]", "### Human", "### Assistant",
    ]

    LM_STUDIO_BASE_URL = "http://localhost:1234"

    @staticmethod
    def _lm_studio_messages_to_parts(messages) -> tuple[str, str, list[str]]:
        """OpenAI-style messages → (system_prompt, user_text, image data URLs).

        Collects every ``image_url`` part (up to 5) in order so R2V can send
        multiple reference images to LM Studio vision.
        """
        system_prompt = ""
        text_parts: list[str] = []
        image_urls: list[str] = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "system":
                system_prompt = content if isinstance(content, str) else str(content or "")
            elif role == "user":
                if isinstance(content, list):
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        if part.get("type") == "text":
                            text_parts.append(part.get("text") or "")
                        elif part.get("type") == "image_url":
                            url = (part.get("image_url") or {}).get("url")
                            if url and len(image_urls) < 5:
                                image_urls.append(url)
                else:
                    text_parts.append(
                        content if isinstance(content, str) else str(content or "")
                    )
        user_text = "".join(text_parts)
        return system_prompt, user_text, image_urls

    @staticmethod
    def _lm_studio_build_v1_input(user_text: str, image_urls: list[str] | str | None):
        """Build LM Studio /api/v1/chat ``input`` with optional multi-image parts."""
        if isinstance(image_urls, str):
            image_urls = [image_urls] if image_urls else []
        image_urls = [u for u in (image_urls or []) if u][:5]
        if image_urls:
            parts = [{"type": "text", "content": user_text}]
            for url in image_urls:
                parts.append({"type": "image", "data_url": url})
            return parts
        return user_text

    @classmethod
    def _lm_studio_post(cls, path: str, body: dict, timeout: int = 300) -> dict:
        url = f"{cls.LM_STUDIO_BASE_URL}{path}"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer lm-studio",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _lm_studio_parse_v1_response(out: dict) -> str:
        parts = []
        for item in out.get("output") or []:
            if isinstance(item, dict) and item.get("type") == "message":
                parts.append(item.get("content") or "")
        return "".join(parts).strip()

    @staticmethod
    def _lm_studio_parse_openai_response(out: dict) -> str:
        choices = out.get("choices")
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(part.get("text") or "")
                elif isinstance(part, str):
                    parts.append(part)
            content = "".join(parts)
        return (content or "").strip()

    @classmethod
    def _lm_studio_try_unload(cls, instance_id: str) -> None:
        """Unload a JIT-loaded model via LM Studio v1 REST API (best-effort)."""
        if not instance_id:
            return
        try:
            cls._lm_studio_post("/api/v1/models/unload", {"instance_id": instance_id})
            print(f"[LazyPrompt] LM Studio JIT model unloaded: {instance_id}")
        except urllib.error.HTTPError as e:
            if e.code in (404, 405, 501):
                print(
                    f"[LazyPrompt] LM Studio unload API unavailable ({e.code}); "
                    "model may remain loaded until manually unloaded."
                )
            else:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                print(
                    f"[LazyPrompt] LM Studio unload failed ({e.code}): "
                    f"{err_body or e.reason}"
                )
        except Exception as e:
            print(f"[LazyPrompt] LM Studio unload failed: {e}")

    def _generate_via_lm_studio_v1(
        self,
        system_prompt: str,
        user_text: str,
        image_urls: list[str] | str | None,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> tuple[str, str | None]:
        body = {
            "model": model_name,
            "input": self._lm_studio_build_v1_input(user_text, image_urls),
            "temperature": temperature,
            "top_p": 0.9,
            "max_output_tokens": max_tokens,
            "store": False,
            "stream": False,
        }
        if system_prompt.strip():
            body["system_prompt"] = system_prompt
        out = self._lm_studio_post("/api/v1/chat", body)
        content = self._lm_studio_parse_v1_response(out)
        if not content:
            raise RuntimeError("[LazyPrompt] LM Studio v1 API returned no message output.")
        instance_id = out.get("model_instance_id") or model_name
        return content, instance_id

    def _generate_via_lm_studio_openai(
        self,
        messages,
        model_name: str,
        temperature: float,
        max_tokens: int,
        stop: list,
        ttl_seconds: int = 0,
    ) -> str:
        body = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop,
            "top_p": 0.9,
            "stream": False,
        }
        if ttl_seconds and ttl_seconds > 0:
            body["ttl"] = int(ttl_seconds)
        out = self._lm_studio_post("/v1/chat/completions", body)
        content = self._lm_studio_parse_openai_response(out)
        if not content:
            raise RuntimeError("[LazyPrompt] LM Studio OpenAI-compatible API returned no choices.")
        return content

    def _generate_via_lm_studio(
        self,
        messages,
        model_name: str,
        temperature: float,
        max_tokens: int,
        stop: list,
        ttl_seconds: int = 0,
    ) -> str:
        """Call LM Studio native v1 REST API, with OpenAI-compatible fallback."""
        system_prompt, user_text, image_urls = self._lm_studio_messages_to_parts(messages)
        unload_instance_id = None

        try:
            result, unload_instance_id = self._generate_via_lm_studio_v1(
                system_prompt=system_prompt,
                user_text=user_text,
                image_urls=image_urls,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print("[LazyPrompt] LM Studio native v1 REST API (/api/v1/chat).")
            if ttl_seconds and ttl_seconds > 0:
                self._lm_studio_try_unload(unload_instance_id)
            return result
        except urllib.error.HTTPError as e:
            if e.code not in (404, 405, 501):
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                raise RuntimeError(
                    f"[LazyPrompt] LM Studio v1 API error ({e.code}): {err_body or e.reason}. "
                    f"Is LM Studio running with the model loaded? Check the model name matches exactly."
                ) from e
            print(
                "[LazyPrompt] LM Studio v1 REST API unavailable; "
                "falling back to OpenAI-compatible /v1/chat/completions."
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[LazyPrompt] LM Studio API error: {e}. Is LM Studio running on localhost:1234 "
                f"with the model loaded? Check the model name matches exactly."
            ) from e

        try:
            result = self._generate_via_lm_studio_openai(
                messages=messages,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                ttl_seconds=ttl_seconds,
            )
            print("[LazyPrompt] LM Studio OpenAI-compatible API (/v1/chat/completions).")
            if ttl_seconds and ttl_seconds > 0:
                self._lm_studio_try_unload(model_name)
            return result
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(
                f"[LazyPrompt] LM Studio API error ({e.code}): {err_body or e.reason}. "
                f"Is LM Studio running with the model loaded? Check the model name matches exactly."
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[LazyPrompt] LM Studio API error: {e}. Is LM Studio running on localhost:1234 "
                f"with the model loaded? Check the model name matches exactly."
            ) from e

    @staticmethod
    def _coerce_creativity(creativity) -> float:
        """Accept float or legacy labeled string presets; clamp to 0.1–1.0."""
        if isinstance(creativity, (int, float)):
            value = float(creativity)
        else:
            text = str(creativity or "").strip()
            legacy = {
                "0.7 - Literal & Grounded": 0.7,
                "0.9 - Balanced Professional": 0.9,
                "1.1 - Artistic Expansion": 1.0,
            }
            if text in legacy:
                value = legacy[text]
            else:
                try:
                    value = float(text.split()[0])
                except (ValueError, IndexError):
                    value = 0.9
        # Round to nearest 0.1 then clamp (LM Studio rejects > 1.0)
        value = round(value * 10) / 10.0
        return max(0.1, min(1.0, value))

    def _generate_via_textgenerate_clip(
        self,
        clip,
        system_prompt: str,
        user_text: str,
        *,
        image=None,
        audio=None,
        max_length: int = 512,
        temperature: float = 0.7,
        seed: int = 0,
        thinking: bool = False,
    ) -> str:
        """Comfy core TextGenerate path: CLIP.tokenize → generate → decode."""
        if clip is None:
            raise ValueError(
                "[LazyPrompt] TextGenerate (CLIP) requires a CLIP input. "
                "Wire CLIPLoader with an LLM-capable model (e.g. Qwen)."
            )

        combined = (
            f"{(system_prompt or '').strip()}\n\n"
            f"{(user_text or '').strip()}\n"
        ).strip()
        if not combined:
            combined = " "

        try:
            from comfy_extras.nodes_textgen import TextGenerate

            sampling_mode = {
                "sampling_mode": "on",
                "temperature": float(temperature),
                "top_k": 64,
                "top_p": 0.95,
                "min_p": 0.05,
                "repetition_penalty": 1.05,
                "seed": int(seed) if seed is not None and int(seed) >= 0 else 0,
                "presence_penalty": 0.0,
            }
            result = TextGenerate.execute(
                clip,
                combined,
                int(max_length),
                sampling_mode,
                image=image,
                thinking=bool(thinking),
                use_default_template=False,
                video=None,
                audio=audio,
            )
            if hasattr(result, "args") and result.args is not None and len(result.args) >= 1:
                text = result.args[0]
            elif isinstance(result, (tuple, list)) and len(result) >= 1:
                text = result[0]
            else:
                text = result
            print("[LazyPrompt] TextGenerate (CLIP) via comfy_extras.nodes_textgen.TextGenerate.")
            return (text or "").strip() if isinstance(text, str) else str(text).strip()
        except ImportError:
            pass
        except Exception as e:
            print(
                f"[LazyPrompt] TextGenerate.execute failed ({e}); "
                "falling back to clip.tokenize/generate/decode."
            )

        try:
            tokens = clip.tokenize(
                combined,
                image=image,
                skip_template=True,
                min_length=1,
                thinking=bool(thinking),
                video=None,
                audio=audio,
            )
        except TypeError:
            try:
                tokens = clip.tokenize(
                    combined, image=image, skip_template=True, min_length=1
                )
            except TypeError:
                tokens = clip.tokenize(combined, image=image)

        gen_seed = int(seed) if seed is not None and int(seed) >= 0 else None
        try:
            generated_ids = clip.generate(
                tokens,
                do_sample=True,
                max_length=int(max_length),
                temperature=float(temperature),
                top_k=64,
                top_p=0.95,
                min_p=0.05,
                repetition_penalty=1.05,
                presence_penalty=0.0,
                seed=gen_seed,
            )
        except TypeError:
            generated_ids = clip.generate(
                tokens,
                do_sample=True,
                max_length=int(max_length),
                temperature=float(temperature),
                top_k=64,
                top_p=0.95,
                seed=gen_seed,
            )
        except AttributeError as e:
            raise RuntimeError(
                "[LazyPrompt] Wired CLIP does not support text generation (.generate). "
                "Load an LLM-capable encoder (Qwen / Gemma / LLaMA), not a plain SD CLIP."
            ) from e

        text = clip.decode(generated_ids)
        print("[LazyPrompt] TextGenerate (CLIP) via clip.tokenize/generate/decode.")
        return (text or "").strip() if isinstance(text, str) else str(text).strip()

    def generate(
        self,
        bypass,
        user_input,
        target_model,
        environment,
        creativity,
        seed,
        keep_model_loaded,
        offline_mode,
        video_length,
        env_seed,
        model,
        local_path_8b,
        local_path_3b,
        lm_studio_model,
        lm_studio_ttl,
        max_output_tokens,
        system_prompt,
        textgenerate_thinking=False,
        clip=None,
        scene_context="",
        lora_triggers="",
        character="",
        first_frame=None,
        image=None,
        last_frame=None,
        reference_image_1=None,
        reference_image_2=None,
        reference_image_3=None,
        reference_image_4=None,
        reference_image_5=None,
        reference_audio=None,
        global_selector_input="",
        SAS_automation_selector_input="",
        prompt_override_input="",
        user_instructions="",
        model_high=None,
        clip_high=None,
        model_low=None,
        clip_low=None,
        # Legacy kwargs from older workflows (ignored)
        screenplay_mode=False,
        invent_dialogue=False,
        fps=0,
    ):
        override_text = (prompt_override_input or "").strip()
        effective_user = override_text or (user_input or "").strip()
        character_text = (character or "").strip()
        if override_text:
            print(
                "[LazyPrompt] prompt_override_input replaces user_input for this LLM request."
            )
        if character_text:
            print("[LazyPrompt] character (subject) prepended to LLM user message.")

        # ── Media gating (global selector / SAS disk override) ────────────────
        sas_blob = (SAS_automation_selector_input or "").strip()
        sel = parse_selector_tagged(sas_blob) if sas_blob else {}
        # Only override direct IMAGE/AUDIO sockets when the blob carries media paths.
        # A Workflow-only blob (common when Global Selector → SAS → PE) must NOT
        # discard wired Lazy Image Loader frames — that was dropping LM Studio vision.
        sas_path_override = any(
            (sel.get(f"referenceimage{i}", "") or "").strip() for i in range(1, 6)
        ) or bool((sel.get("audioreference", "") or "").strip())

        mode = resolve_mode_from_selector(sas_blob) if sas_blob else None
        if not mode:
            mode = resolve_mode_from_selector(global_selector_input or "")

        if sas_path_override:
            print(
                "[LazyPrompt] SAS selector has ReferenceImage/AudioReference paths — "
                "loading media from disk; ignoring direct image/audio sockets."
            )
            ff = _load_image_tensor_from_input(sel.get("referenceimage1", ""))
            lf = _load_image_tensor_from_input(sel.get("referenceimage2", ""))
            refs = [
                _load_image_tensor_from_input(sel.get(f"referenceimage{i}", ""))
                for i in range(1, 6)
            ]
            audio = _load_audio_dict_from_input(sel.get("audioreference", ""))
            if mode in ("I2V", "FL2V", None):
                if ff is None and refs[0] is not None:
                    ff = refs[0]
                if lf is None and refs[1] is not None:
                    lf = refs[1]
            out_first, out_last, out_refs, out_audio, mode = _gate_media_for_mode(
                mode, ff, lf, refs, audio, sas_override=True
            )
        else:
            ff = first_frame if first_frame is not None else image
            refs = [
                reference_image_1,
                reference_image_2,
                reference_image_3,
                reference_image_4,
                reference_image_5,
            ]
            out_first, out_last, out_refs, out_audio, mode = _gate_media_for_mode(
                mode, ff, last_frame, refs, reference_audio, sas_override=False
            )
            if sas_blob and not sas_path_override:
                print(
                    "[LazyPrompt] SAS selector has mode/tags but no media paths — "
                    f"using direct sockets (first_frame={'yes' if ff is not None else 'no'})."
                )

        if not mode:
            # Infer from what survived / was provided
            if any(r is not None for r in out_refs) or out_audio is not None:
                mode = "R2V"
            elif out_first is not None and out_last is not None:
                mode = "FL2V"
            elif out_first is not None:
                mode = "I2V"
            else:
                mode = "T2V" if (global_selector_input or sas_blob) else ""

        selector_out = mode or resolve_mode_from_selector(global_selector_input or "") or ""

        def _pack(prompt_text, preview_text, neg_text):
            # After LLM (or bypass): apply Prompt [LoraH]/[LoraL] to stacks, strip tags
            # so the diffusion model never sees the loader markers.
            clean, mh, ml, ch, cl = apply_prompt_lora_blocks(
                prompt_text,
                model_high=model_high,
                clip_high=clip_high,
                model_low=model_low,
                clip_low=clip_low,
                also_collect_from=effective_user,
            )
            # preview_text matches prompt_text in all current call sites; strip both.
            preview_clean = (
                clean
                if preview_text == prompt_text
                else parse_and_strip_prompt_loras(preview_text or "")[0]
            )
            return (
                clean,
                preview_clean,
                neg_text,
                selector_out,
                out_first,
                out_last,
                out_refs[0],
                out_refs[1],
                out_refs[2],
                out_refs[3],
                out_refs[4],
                out_audio,
                mh,
                ml,
                ch,
                cl,
            )

        # Vision payloads for LM Studio / TextGenerate:
        # - I2V: first frame
        # - FL2V: first + last frame
        # - R2V: all connected reference_image_1..5 (socket index = <Picture N>)
        vision_images: list[tuple[int, object]] = []
        if mode == "R2V":
            for i, r in enumerate(out_refs):
                if r is not None:
                    vision_images.append((i + 1, r))
        else:
            if out_first is not None:
                vision_images.append((1, out_first))
            if mode == "FL2V" and out_last is not None:
                vision_images.append((2, out_last))
        vision_image = vision_images[0][1] if vision_images else None

        # ── Bypass mode — no model loaded, input passed straight through ────────
        if bypass:
            print("[LazyPrompt] Bypass ON — skipping model, passing user_input directly.")
            neg_prompt = _build_negative_prompt("", effective_user)
            return _pack(effective_user, effective_user, neg_prompt)

        use_lm_studio = model == "LM Studio (API)"
        use_textgenerate = model == "TextGenerate (CLIP)"
        if vision_images and not use_lm_studio and not use_textgenerate:
            print(
                "[LazyPrompt] IMAGE input is sent with LM Studio (API) or TextGenerate (CLIP). "
                "Switch backend, or use scene_context from LazyPrompt — Vision Describe."
            )
        if use_textgenerate:
            if clip is None:
                raise ValueError(
                    "[LazyPrompt] When using TextGenerate (CLIP), wire an LLM-capable CLIP "
                    "into the clip input (CLIPLoader → Qwen / Gemma / etc.)."
                )
        elif use_lm_studio:
            if not (lm_studio_model and lm_studio_model.strip()):
                raise ValueError(
                    "[LazyPrompt] When using LM Studio (API), enter the model name in the "
                    "'lm_studio_model' field. LM Studio must be running with that model loaded."
                )
        else:
            path_map = {
                "8B - NeuralDaredevil (High Quality)": local_path_8b,
                "3B - Llama-3.2 Abliterated (Low VRAM)": local_path_3b,
            }
            local_path = path_map.get(model, "")
            self.load_model(model_key=model, offline_mode=offline_mode, local_path=local_path)

        is_vid = is_video_model(target_model)

        # None target + system_prompt override and/or scenario prompt_override_input:
        # send only the user/override text to the LLM (no aug block, no user_tail injections).
        minimal_llm = is_none_target(target_model) and (
            bool((system_prompt or "").strip()) or bool(override_text)
        )

        max_tokens_actual = max(96, min(int(max_output_tokens), _ABS_MAX_OUTPUT_TOKENS))
        reply_target = max(32, max_tokens_actual // 3)

        # --- Video: length in seconds only; beats derived from duration ---
        if is_vid:
            real_seconds = max(float(video_length), 0.25)
            action_count = max(1, min(10, round(real_seconds / 4)))
            if action_count == 1:
                pacing_hint = (
                    f"This clip is {real_seconds:.0f} seconds long. "
                    f"Write EXACTLY 1 action. One single moment. "
                    f"Do not describe anything before or after it. No setup, no resolution. "
                    f"HARD STOP after the 1st action. Do not continue."
                )
            else:
                ordinal = {2: "2nd", 3: "3rd"}.get(action_count, f"{action_count}th")
                pacing_hint = (
                    f"This clip is {real_seconds:.0f} seconds long. "
                    f"Write EXACTLY {action_count} distinct actions — NO MORE THAN {action_count}. "
                    f"Each action takes roughly {real_seconds / action_count:.0f} seconds of screen time. "
                    f"Do not add setup, backstory, or resolution beyond these {action_count} actions. "
                    f"Dialogue counts as an action if it interrupts the physical scene — budget it inside one of your {action_count} beats, not as an extra beat. "
                    f"HARD STOP after the {ordinal} action is complete. The scene ends there. Do not write a {action_count + 1}th action under any circumstances."
                )
            min_tokens = max(
                16,
                min(int(reply_target * 0.75), max_tokens_actual - 1),
            )
            length_instruction = (
                f"\n[PACING — THIS IS MANDATORY: {pacing_hint} "
                f"Write approximately {reply_target} tokens total (hard cap {max_tokens_actual} new tokens). "
                f"Do not exceed the action count above under any circumstances. "
                f"Do NOT write the token count, word count, action number, or any parenthetical summary, checklist, or compliance note at the end — "
                f"the scene ends with the last sentence of prose. Nothing after it. No brackets. No notes. No confirmation.]"
            )
            print(
                f"[LazyPrompt] Video tokens: ~{reply_target} pacing target / {max_tokens_actual} max new tokens "
                f"(actions: {action_count}, length: {real_seconds:g}s)"
            )
        else:
            real_seconds = 0.0
            action_count = 1
            min_tokens = max(
                16,
                min(int(reply_target * 0.75), max_tokens_actual - 1),
            )
            length_instruction = (
                "\n[FORMAT: Follow the system prompt exactly for the image target. "
                f"Aim for roughly {reply_target} tokens of descriptive output (hard cap {max_tokens_actual} new tokens). "
                "No preamble, no meta commentary in your reply.]\n"
            )
            print(
                f"[LazyPrompt] Image tokens: ~{reply_target} pacing target / {max_tokens_actual} max new tokens"
            )

        # --- Seed ---
        if seed != -1:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)

        # --- Temperature ---
        temperature = self._coerce_creativity(creativity)

        # --- Build stop token list (HF path only) ---
        # This encodes every known role delimiter into actual token IDs so the
        # model hard-stops before it can write "assistant" or any turn boundary.
        if not use_lm_studio and not use_textgenerate:
            stop_token_ids = self._build_stop_token_ids()

        # --- Content tier detection ---
        # Three tiers based on what the user actually asked for.
        # Tier 1 — Neutral:  no nudity/sex words → no explicit instruction
        # Tier 2 — Sensual:  nudity/undressing implied but no anatomical terms
        #                    → restrain the model from self-escalating
        # Tier 3 — Explicit: user used anatomical terms → full explicit instruction

        # Tier 3 triggers: direct anatomical / act terms
        _explicit_re = re.compile(
            r"\b(pussy|cock|dick|penis|vagina|clit|clitoris|anus|asshole|"
            r"tits|cum|orgasm|fuck|fucking|blowjob|handjob|penetrat\w*|"
            r"thrust\w*)\b",
            re.IGNORECASE,
        )

        # Tier 2 triggers: nudity/sensuality implied but not explicit
        _sensual_re = re.compile(
            r"\b(naked|nude|topless|undress\w*|strip\w*|takes?\s+off|"
            r"removes?\s+(her|his|their|the)?\s*\w*\s*"
            r"(shirt|dress|top|bra|pants|jeans|clothes|clothing|outfit|underwear|skirt|jacket|coat|robe)|"
            r"disrobe\w*|unbutton\w*|unzip\w*|peels?\s+off|pulls?\s+off|"
            r"shed\w*\s+(her|his|their)?\s*(clothes|clothing|shirt|dress)|"
            r"sensual|erotic|intimate|lingerie|bare\s+skin|bare\s+body)\b",
            re.IGNORECASE,
        )

        is_explicit    = bool(_explicit_re.search(effective_user + " " + character_text))
        is_sensual     = bool(_sensual_re.search(effective_user + " " + character_text)) and not is_explicit

        # Undressing detection still used inside tier 3 for the mandatory segment rule
        _undress_re = re.compile(
            r"\b(undress\w*|strip\w*|takes?\s+off|"
            r"removes?\s+(her|his|their|the)?\s*\w*\s*"
            r"(shirt|dress|top|bra|pants|jeans|clothes|clothing|outfit|underwear|skirt|jacket|coat|robe)|"
            r"disrobe\w*|unbutton\w*|unzip\w*|peels?\s+off|pulls?\s+off|"
            r"shed\w*\s+(her|his|their)?\s*(clothes|clothing|shirt|dress))\b",
            re.IGNORECASE,
        )
        has_undressing = bool(_undress_re.search(effective_user + " " + character_text))

        if is_explicit:
            # ── Tier 3: user asked for explicit content ──────────────────────
            explicit_instruction = (
                "\n[INSTRUCTION: This is an explicit adult scene. "
                "You MUST use direct anatomical terms — pussy, cock, anus, clit, ass — exactly as written. "
                "These are REQUIRED words, not optional. Do not replace them with 'sex', 'crevice', 'core', "
                "'womanhood', 'manhood', or any other euphemism or metaphor. "
                "If the user said 'pussy', write 'pussy' every time. "
                "UNDRESSING SEGMENT — MANDATORY: If the subject starts clothed, you MUST write a dedicated undressing segment "
                "before ANY explicit act or nudity. This is not a brief mention — it is a full narrative beat. "
                "Go garment by garment: name it, describe how it is removed (fingers, zipper, pulling over the head, stepping out of), "
                "describe what body part is revealed and how it looks. Then the next garment. Then the next. "
                "The camera must linger on each reveal. Do not compress. Do not summarise. Do not skip to naked. "
                "The undressing IS the scene — write it with the same density and length as the explicit act that follows. "
                "Always state the character's age as a specific number. "
                "Describe body parts, positions, and physical actions with blunt, specific language. "
                "Every anatomical detail must be stated plainly — no softening, no implying, no cutting away.]"
            )
        elif is_sensual:
            # ── Tier 2: nudity/undressing implied — sensual but not pornographic ─
            undress_clause = (
                "UNDRESSING SEGMENT — MANDATORY: The prompt involves clothing removal or nudity. "
                "Write a dedicated undressing segment as its own narrative beat — garment by garment, "
                "describing how each is removed and what is physically revealed at each step. "
                "The camera lingers on each reveal. Do not skip or compress. "
                "Describing bare skin, curves, and the naked body is appropriate and expected. "
            ) if has_undressing else ""
            explicit_instruction = (
                "\n[INSTRUCTION: This scene involves nudity or sensual content. "
                "Describing the bare body naturally is appropriate — skin, curves, flesh, nakedness. "
                "However, do NOT zoom in on or explicitly describe genitals. "
                "Do NOT introduce sexual acts the user did not ask for. "
                "Do NOT self-escalate beyond what the user described. "
                "Keep the tone sensual and cinematic — not pornographic. "
                "Always state the character's age as a specific number. "
                + undress_clause + "]"
            )
        else:
            # ── Tier 1: neutral — just enforce age rule ──────────────────────
            explicit_instruction = (
                "\n[INSTRUCTION: Always state the character's age as a specific number, "
                "e.g. 'a 34-year-old man' — never omit or approximate it.]"
            )


        # --- Sequence detection ---
        # If the user wrote numbered steps (1. 2. 3. etc), detect them and inject
        # an instruction to follow that exact order — no reordering, no skipping.
        _sequence_re = re.compile(
            r"^\s*(\d+[\.\):])\s+.+", re.MULTILINE
        )
        sequence_steps = _sequence_re.findall(effective_user)
        if len(sequence_steps) >= 2:
            step_count = len(sequence_steps)
            sequence_instruction = (
                f"\n[SEQUENCE INSTRUCTION: The user has provided {step_count} numbered steps. "
                f"You MUST follow them in exact order — step 1 first, then step 2, and so on. "
                f"Do not reorder, skip, or merge steps. Each step is one distinct beat in the scene. "
                f"Do not add actions before step 1 or after step {step_count}.]"
            )
        else:
            sequence_instruction = ""

        # --- Person detection ---
        # If the input contains no reference to a person, inject an instruction
        # telling the model to write a pure scene — no invented characters.
        _person_re = re.compile(
            r"\b(he|she|his|her|him|they|them|their|man|men|woman|women|girl|girls|boy|boys|guy|guys|"
            r"person|people|couple|figure|character|model|actress|actor|"
            r"someone|anybody|nobody|stranger|friend|lover|wife|husband|"
            r"boyfriend|girlfriend|teenager|teenagers|adult|adults|female|male|blonde|brunette|"
            r"redhead|nude|naked|singer|dancer|performer|athlete|soldier|worker|"
            r"player|nurse|doctor|student|teacher|child|children|kid|kids|crowd|audience)\b",
            re.IGNORECASE,
        )
        _context_for_detection = effective_user + " " + (scene_context or "") + " " + character_text
        has_person = bool(_person_re.search(_context_for_detection))
        if not has_person:
            no_person_instruction = (
                "\n[SCENE INSTRUCTION: The user has not described any person or character. "
                "Do NOT invent or introduce any human figures, silhouettes, voices, or implied presence. "
                "This is a pure environment or object scene. Write only what the user described — "
                "the setting, objects, light, atmosphere, and motion of non-human elements. "
                "No characters. No 'someone', no 'a figure', no implied human presence of any kind. "
                "No dialogue, no whispers, no voices. Sound is limited to the environment only — "
                "wind, rain, fire, machinery, animals, ambient room tone. Nothing with a human source.]"
            )
        else:
            no_person_instruction = ""

        # --- Multi-subject detection ---
        # If the input describes two or more people, inject a spatial instruction
        # so the model tracks who is doing what and where they are relative to
        # each other and the camera — otherwise it tends to lose track.
        _multi_re = re.compile(
            r"\b(two\s+(women|men|people|girls|guys|characters|figures)|"
            r"both\s+(of\s+them|women|men|girls|guys)|"
            r"(she|he)\s+and\s+(she|he|her|him)|"
            r"(a\s+man\s+and\s+a\s+woman|a\s+woman\s+and\s+a\s+man)|"
            r"(a\s+man\s+and\s+a\s+man|a\s+woman\s+and\s+a\s+woman)|"
            r"couple|trio|they\s+(kiss|touch|embrace|undress|fuck|have))\b",
            re.IGNORECASE,
        )
        has_multi_subject = bool(_multi_re.search(_context_for_detection))
        if has_multi_subject:
            multi_instruction = (
                "\n[MULTI-SUBJECT INSTRUCTION: This scene has two or more people. "
                "For EACH person establish: their position in the frame (left/right/foreground/background), "
                "their spatial relationship to the other person (facing, beside, behind, above, etc.), "
                "and keep track of who is doing what throughout — never let actions become ambiguous. "
                "When referring back to them use consistent descriptors (e.g. 'the dark-haired woman', "
                "'the taller man') — not just 'she' or 'he' which causes confusion with two subjects.]"
            )
        else:
            multi_instruction = ""

        # Dialogue rules live in Model_Skills/*.md (e.g. LTX 2.3 Dialog) — no runtime invent_dialogue toggle.

        # --- Scene / subject / user direction (always in LLM user message) ---
        effective_input = compose_user_scene_input(
            effective_user,
            scene_context=scene_context or "",
            character=character_text,
            target_model=target_model,
        )

        if minimal_llm:
            parts = []
            if (system_prompt or "").strip():
                parts.append("system_prompt")
            if override_text:
                parts.append("prompt_override_input")
            if character_text:
                parts.append("character")
            print(
                f"[LazyPrompt] Minimal mode (None target + {' + '.join(parts)}): "
                "no augmentation block or user_tail injections."
            )
        else:
            has_visual_context = bool(scene_context and scene_context.strip()) or (
                (use_lm_studio or use_textgenerate) and bool(vision_images)
            )
            aug = build_prompt_augmentation(
                target_model=target_model,
                environment=environment,
                video_length_sec=real_seconds if is_vid else 0.0,
                seed=env_seed,
                has_scene_context=has_visual_context,
            )
            if aug.strip():
                effective_input = effective_input.rstrip() + "\n\n---\n" + aug

        # --- LoRA trigger injection ---
        # If the user provided trigger words, inject them as a hard instruction
        # so they appear at the start of the final prompt and are never buried.
        if lora_triggers and lora_triggers.strip():
            lora_instruction = (
                f"\n[LORA INSTRUCTION: You MUST begin the prompt output with these exact trigger words "
                f"before anything else: {lora_triggers.strip()} — place them as the very first words of your output, "
                f"then continue with the scene description immediately after.]"
            )
        else:
            lora_instruction = ""

        # --- System prompt: override or Model_Skills template for target_model ---
        base_system = (system_prompt.strip() if system_prompt else "") or get_system_prompt(
            target_model
        )
        effective_system_prompt = apply_user_prompt_injection(
            base_system, user_instructions or ""
        )
        if (user_instructions or "").strip():
            print("[LazyPrompt] user_instructions injected into ***UserPrompt*** block.")

        if minimal_llm:
            user_tail = ""
        else:
            user_tail = (
                sequence_instruction
                + no_person_instruction
                + multi_instruction
                + explicit_instruction
                + lora_instruction
                + length_instruction
            )
        user_text = effective_input + user_tail
        if use_lm_studio and vision_images:
            try:
                content_parts = [{"type": "text", "text": user_text}]
                if mode == "R2V":
                    pic_tags = ", ".join(f"<Picture {n}>" for n, _ in vision_images)
                    content_parts.append(
                        {
                            "type": "text",
                            "text": (
                                f"\n\n[VISION: {len(vision_images)} reference image(s) "
                                f"attached in socket order: {pic_tags}]"
                            ),
                        }
                    )
                for n, tensor in vision_images:
                    data_url = _comfy_image_to_jpeg_data_url(tensor)
                    if mode == "R2V":
                        content_parts.append(
                            {"type": "text", "text": f"\n[<Picture {n}>]"}
                        )
                    content_parts.append(
                        {"type": "image_url", "image_url": {"url": data_url}}
                    )
            except Exception as e:
                raise RuntimeError(
                    f"[LazyPrompt] Failed to encode IMAGE for LM Studio: {e}"
                ) from e
            messages = [
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": content_parts},
            ]
            print(
                f"[LazyPrompt] LM Studio request includes vision "
                f"({len(vision_images)} image(s))."
            )
        else:
            messages = [
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": user_text},
            ]

        # ── TextGenerate (CLIP) path: Comfy core Generate Text ────────────────
        if use_textgenerate:
            tg_seed = int(seed) if seed is not None and int(seed) >= 0 else 0
            result = self._generate_via_textgenerate_clip(
                clip,
                effective_system_prompt,
                user_text,
                image=vision_image,
                audio=out_audio if mode == "R2V" else None,
                max_length=max_tokens_actual,
                temperature=temperature,
                seed=tg_seed,
                thinking=bool(textgenerate_thinking),
            )
            result = self._clean_output(result)
            result, neg_prompt = self._finalize_output(target_model, result, effective_user)
            return _pack(result, result, neg_prompt)

        # ── LM Studio path: API call then same post-process ───────────────────
        if use_lm_studio:
            result = self._generate_via_lm_studio(
                messages=messages,
                model_name=lm_studio_model.strip(),
                temperature=temperature,
                max_tokens=max_tokens_actual,
                stop=self.LM_STUDIO_STOP,
                ttl_seconds=int(lm_studio_ttl or 0),
            )
            result = self._clean_output(result)
            result, neg_prompt = self._finalize_output(target_model, result, effective_user)
            return _pack(result, result, neg_prompt)

        # ── HuggingFace path: tokenize, generate, decode ──────────────────────
        # apply_chat_template returns different types depending on the
        # transformers version and tokenizer implementation:
        #   - Plain tensor          (older transformers, most common)
        #   - BatchEncoding object  (newer transformers 4.43+, has .input_ids)
        #   - Plain dict            (some tokenizer variants)
        #   - Plain Python list     (some versions ignore return_tensors entirely)
        # We normalise all four cases into a plain LongTensor before calling .shape.
        raw = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True,
        )
        if hasattr(raw, "input_ids"):
            # BatchEncoding object (transformers 4.43+)
            input_ids = raw.input_ids.to(self.model.device)
        elif isinstance(raw, dict):
            # Plain dict with input_ids key
            input_ids = raw["input_ids"].to(self.model.device)
        elif isinstance(raw, list):
            # return_tensors was ignored — wrap flat list into tensor
            input_ids = torch.tensor([raw], dtype=torch.long).to(self.model.device)
        else:
            # Already a plain tensor — normal case
            input_ids = raw.to(self.model.device)

        input_length = input_ids.shape[1]

        with torch.no_grad():
            output_ids = self.model.generate(
                input_ids,
                min_new_tokens=min_tokens,
                max_new_tokens=max_tokens_actual,
                temperature=temperature,
                do_sample=True,
                top_k=40,
                top_p=0.9,
                repetition_penalty=1.07,
                use_cache=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=stop_token_ids,   # hard-stop on ANY delimiter
            )

        # Slice ONLY newly generated tokens
        generated_tokens = output_ids[0][input_length:]

        result = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        ).strip()

        del output_ids
        del input_ids

        # Regex clean as a last-resort safety net (should rarely trigger now)
        result = self._clean_output(result)

        result, neg_prompt = self._finalize_output(target_model, result, effective_user)

        if not keep_model_loaded:
            self.unload_model()

        return _pack(result, result, neg_prompt)


# ── ComfyUI boilerplate ──────────────────────────────────────────────────────

class LazyPromptUnloadModel:
    """Free VRAM from LazyPromptEngineer when keep_model_loaded was left on."""

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "unload"
    CATEGORY = "vsaan212/LazyPrompt"
    OUTPUT_NODE = True

    def unload(self):
        import gc

        unloaded = 0
        for obj in gc.get_objects():
            if isinstance(obj, LazyPromptEngineer) and obj.model is not None:
                obj.unload_model()
                unloaded += 1
        print(f"[LazyPrompt] Unload node: freed {unloaded} model instance(s).")
        return {}


NODE_CLASS_MAPPINGS = {
    "LazyPromptEngineer": LazyPromptEngineer,
    "LazyPromptUnloadModel": LazyPromptUnloadModel,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyPromptEngineer": "LazyPrompt — Prompt Engineer",
    "LazyPromptUnloadModel": "LazyPrompt — Unload local model",
}
