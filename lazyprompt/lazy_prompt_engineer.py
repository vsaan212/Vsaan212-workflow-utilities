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
from .message_builder import build_prompt_augmentation, split_positive_negative_block
from .system_prompts import (
    JSON_PROMPTS_HINT,
    TARGET_MODEL_DEFAULT,
    TARGET_MODELS,
    default_fps_for_target,
    get_system_prompt,
    is_none_target,
    is_video_model,
)


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
        return {
            "required": {
                "bypass": ("BOOLEAN", {"default": False, "tooltip": "When ON, skips the LLM entirely and sends your text straight through. Use for manual prompts or testing."}),
                "user_input": ("STRING", {
                    "multiline": True,
                    "default": "a woman walks through a rain-soaked city street at night",
                    "tooltip": "Rough idea, sentence, or numbered steps. The LLM expands into a prompt for the selected target model.",
                }),
                "target_model": (
                    TARGET_MODELS,
                    {
                        "default": TARGET_MODEL_DEFAULT,
                        "tooltip": (
                            "Prompt style: LTX / Wan (video), Flux / SDXL / Pony / SD 1.5 (image). "
                            '"None" = no JSON template (empty system unless override). '
                            + JSON_PROMPTS_HINT
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
                "screenplay_mode": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "LTX 2.3 only: screenplay-style character/scene/beats. Ignored for other targets.",
                    },
                ),
                "creativity": ([
                    "0.7 - Literal & Grounded",
                    "0.9 - Balanced Professional",
                    "1.1 - Artistic Expansion",
                ], {"default": "0.9 - Balanced Professional", "tooltip": "Sampling temperature preset for local HF models and LM Studio."}),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2**31 - 1,
                    "step": 1,
                    "display": "number",
                    "tooltip": "LLM seed. -1 = random each run.",
                }),
                "invent_dialogue": ("BOOLEAN", {"default": True, "tooltip": "Video targets: when ON, invent inline dialogue; when OFF, only quoted user dialogue or silence."}),
                "keep_model_loaded": ("BOOLEAN", {"default": False, "tooltip": "Keep the local HF model in VRAM between runs. Off frees VRAM after each run."}),
                "offline_mode": ("BOOLEAN", {"default": False, "tooltip": "ON = no HuggingFace network; local cache / paths only."}),
                "video_length": ("FLOAT", {
                    "default": 8.0,
                    "min": 0.25,
                    "max": 300.0,
                    "step": 0.25,
                    "display": "number",
                    "tooltip": "Video duration in seconds (video targets). Frame count for hints = length × fps. Image targets ignore this.",
                }),
                "fps": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 60,
                    "step": 1,
                    "display": "number",
                    "tooltip": "0 = auto from target model (Wan 16, LTX 25, else 24). Set >0 to override.",
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
                ], {"default": "LM Studio (API)", "tooltip": "Backend LLM: local HF checkpoints or LM Studio REST API (native /api/v1/chat with OpenAI fallback)."}),
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
                    "tooltip": "LM Studio OpenAI fallback only: idle seconds before JIT-loaded model unloads (JSON ttl). 0 = omit. Ignored on native /api/v1/chat.",
                }),
                "max_output_tokens": ("INT", {
                    "default": 900,
                    "min": 96,
                    "max": _ABS_MAX_OUTPUT_TOKENS,
                    "step": 16,
                    "display": "number",
                    "tooltip": (
                        "Hard cap on completion length (HF max_new_tokens / LM Studio max_tokens). "
                        "The pacing hint asks the model for ~one-third of this many tokens by default — "
                        "raise both together for longer prompts (e.g. 1500 max → ~500 target)."
                    ),
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Leave empty = JSON template for target_model",
                    "tooltip": (
                        "Override system prompt. If empty, uses lazyprompt/system_prompts.json for the selected target. "
                        "When target is None and this field has text, only that text is used as system prompt and the "
                        "user message is scene + idea only (no auto augmentation). "
                        + JSON_PROMPTS_HINT
                    ),
                }),
            },
            "optional": {
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
                    "placeholder": "Character / LoRA lock description",
                    "tooltip": "Merged into the request as a hard character lock (natural language or tags per target).",
                }),
                "image": ("IMAGE", {
                    "tooltip": (
                        "Optional. For use with LM Studio (API) and a vision-enabled model loaded in LM Studio. "
                        "Sends this frame as an image alongside your text (OpenAI-style multimodal chat). "
                        "Ignored when using local Hugging Face text-only models — use LazyPrompt — Vision Describe + scene_context instead."
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
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("PROMPT", "PREVIEW", "NEG_PROMPT")
    FUNCTION = "generate"
    CATEGORY = "vsaan212/LazyPrompt"

    # ── Model registry ───────────────────────────────────────────────────────
    # Maps dropdown label → HuggingFace model ID for auto-download
    MODELS = {
        "8B - NeuralDaredevil (High Quality)": "mlabonne/NeuralDaredevil-8B-abliterated",
        "3B - Llama-3.2 Abliterated (Low VRAM)": "huihui-ai/Llama-3.2-3B-Instruct-abliterated",
    }

    # Default target templates: lazyprompt/system_prompts.json (editable)

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
        if any(x in target_model for x in ("SDXL", "Pony", "SD 1.5")):
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
    def _lm_studio_messages_to_parts(messages) -> tuple[str, str, str | None]:
        """OpenAI-style messages → (system_prompt, user_text, optional image data URL)."""
        system_prompt = ""
        user_text = ""
        image_url = None
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
                            user_text = part.get("text") or ""
                        elif part.get("type") == "image_url":
                            image_url = (part.get("image_url") or {}).get("url")
                else:
                    user_text = content if isinstance(content, str) else str(content or "")
        return system_prompt, user_text, image_url

    @staticmethod
    def _lm_studio_build_v1_input(user_text: str, image_url: str | None):
        if image_url:
            return [
                {"type": "text", "content": user_text},
                {"type": "image", "data_url": image_url},
            ]
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

    def _generate_via_lm_studio_v1(
        self,
        system_prompt: str,
        user_text: str,
        image_url: str | None,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        body = {
            "model": model_name,
            "input": self._lm_studio_build_v1_input(user_text, image_url),
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
        return content

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
        system_prompt, user_text, image_url = self._lm_studio_messages_to_parts(messages)

        try:
            result = self._generate_via_lm_studio_v1(
                system_prompt=system_prompt,
                user_text=user_text,
                image_url=image_url,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print("[LazyPrompt] LM Studio native v1 REST API (/api/v1/chat).")
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

    def generate(
        self,
        bypass,
        user_input,
        target_model,
        environment,
        screenplay_mode,
        creativity,
        seed,
        invent_dialogue,
        keep_model_loaded,
        offline_mode,
        video_length,
        fps,
        env_seed,
        model,
        local_path_8b,
        local_path_3b,
        lm_studio_model,
        lm_studio_ttl,
        max_output_tokens,
        system_prompt,
        scene_context="",
        lora_triggers="",
        character="",
        image=None,
        prompt_override_input="",
    ):
        override_text = (prompt_override_input or "").strip()
        effective_user = override_text or (user_input or "").strip()
        if override_text:
            print(
                "[LazyPrompt] prompt_override_input replaces user_input for this LLM request."
            )

        # ── Bypass mode — no model loaded, input passed straight through ────────
        if bypass:
            print("[LazyPrompt] Bypass ON — skipping model, passing user_input directly.")
            neg_prompt = _build_negative_prompt("", effective_user)
            return (effective_user, effective_user, neg_prompt)

        use_lm_studio = model == "LM Studio (API)"
        if image is not None and not use_lm_studio:
            print(
                "[LazyPrompt] IMAGE input is only sent to LM Studio (API) with a vision-capable model. "
                "Switch backend to LM Studio, or use scene_context from LazyPrompt — Vision Describe."
            )
        if use_lm_studio:
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
        screen_use = bool(screenplay_mode and "LTX" in target_model)
        fps_f = float(fps) if int(fps) > 0 else default_fps_for_target(target_model)

        # None target + non-empty system override → system comes only from override; user message has no aug/tail
        minimal_llm = is_none_target(target_model) and (system_prompt or "").strip()

        max_tokens_actual = max(96, min(int(max_output_tokens), _ABS_MAX_OUTPUT_TOKENS))
        reply_target = max(32, max_tokens_actual // 3)

        # --- Video: length in seconds × fps → frame count for LLM hints; beats from seconds ---
        if is_vid:
            real_seconds = max(float(video_length), 0.25)
            frame_count = int(round(real_seconds * fps_f))
            frame_count = max(1, min(frame_count, 2000))
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
                f"(actions: {action_count}, length: {real_seconds:g}s, frames≈{frame_count}, fps: {fps_f:g})"
            )
        else:
            real_seconds = 0.0
            frame_count = 0
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
        temp_map = {
            "0.7 - Literal & Grounded":    0.7,
            "0.9 - Balanced Professional": 0.9,
            "1.1 - Artistic Expansion":    1.1,
        }
        temperature = temp_map[creativity]

        # --- Build stop token list (HF path only) ---
        # This encodes every known role delimiter into actual token IDs so the
        # model hard-stops before it can write "assistant" or any turn boundary.
        if not use_lm_studio:
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

        is_explicit    = bool(_explicit_re.search(effective_user))
        is_sensual     = bool(_sensual_re.search(effective_user)) and not is_explicit

        # Undressing detection still used inside tier 3 for the mandatory segment rule
        _undress_re = re.compile(
            r"\b(undress\w*|strip\w*|takes?\s+off|"
            r"removes?\s+(her|his|their|the)?\s*\w*\s*"
            r"(shirt|dress|top|bra|pants|jeans|clothes|clothing|outfit|underwear|skirt|jacket|coat|robe)|"
            r"disrobe\w*|unbutton\w*|unzip\w*|peels?\s+off|pulls?\s+off|"
            r"shed\w*\s+(her|his|their)?\s*(clothes|clothing|shirt|dress))\b",
            re.IGNORECASE,
        )
        has_undressing = bool(_undress_re.search(effective_user))

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
        has_person = bool(_person_re.search(effective_user + " " + scene_context))
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
        has_multi_subject = bool(_multi_re.search(effective_user + " " + scene_context))
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

        # --- Dialogue instruction (video targets only) ---
        if not is_vid:
            dialogue_instruction = ""
        elif not has_person:
            dialogue_instruction = ""  # no_person_instruction already covers this
        elif invent_dialogue:
            dialogue_instruction = (
                "\n\n[DIALOGUE INSTRUCTION: Invent dialogue that fits this scene naturally. "
                "Write it as inline prose woven into the action — NOT as a [DIALOGUE: ...] tag or bracketed block. "
                "The spoken words sit inside the sentence with attribution and physical delivery, like a novel. "
                "Examples: "
                "'He leans back, satisfied, \"I think I\\'ll have to go back tomorrow for more,\" he chuckles, his eyes crinkling at the corners.' "
                "'\"Don\\'t stop,\" she breathes, gripping the sheets, her voice barely above a whisper.' "
                "If the scene is sexual or explicit, dialogue must reflect that — breathless, reactive, commanding. "
                "Never write a bare floating quote. Never use [DIALOGUE: ...] tags. Dialogue is part of the prose, always.]"
            )
        else:
            has_user_dialogue = bool(re.search(r'["\u201c\u201d]', effective_user))
            if has_user_dialogue:
                dialogue_instruction = (
                    "\n\n[DIALOGUE INSTRUCTION: Use ONLY the dialogue the user provided — do not invent or add any additional spoken words. "
                    "Place their exact words naturally in the scene as inline prose with attribution and delivery. "
                    "Examples: 'She smiles, \"I\\'m so happy,\" her voice bright, eyes wide.' "
                    "'\"I\\'m so happy,\" he whispers, pulling her close, his voice low.' "
                    "Never use [DIALOGUE: ...] tags. Weave the words into the action as part of the prose.]"
                )
            else:
                dialogue_instruction = (
                    "\n\n[DIALOGUE INSTRUCTION: No dialogue in this scene. No spoken words. "
                    "Weave ambient sound naturally into the prose instead — maximum 2 sounds active at any one time, "
                    "woven in as descriptive prose, not as tags.]"
                )

        # --- Merge vision context if provided ---
        # When a scene_context is wired in from the Vision Describe node,
        # prepend it so the LLM uses it as the authoritative subject/scene
        # description rather than inventing one from scratch.
        if scene_context and scene_context.strip():
            effective_input = (
                f"[SCENE CONTEXT FROM IMAGE — use this as the authoritative description "
                f"of the subject and setting; do not invent or contradict it]\n"
                f"{scene_context.strip()}\n\n"
                f"[USER DIRECTION — apply this as action, style, and mood over the above scene]\n"
                f"{effective_user}"
            )
        else:
            effective_input = effective_user

        if minimal_llm:
            print(
                "[LazyPrompt] Minimal mode (None target + system override): "
                "system prompt from override only; user message is scene + idea only (no augmentation tail)."
            )
        else:
            has_visual_context = bool(scene_context and scene_context.strip()) or (
                use_lm_studio and image is not None
            )
            aug = build_prompt_augmentation(
                target_model=target_model,
                environment=environment,
                frame_count=frame_count,
                fps=fps_f,
                character=(character or "").strip(),
                seed=env_seed,
                screenplay_mode=screen_use,
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

        # --- System prompt: override or JSON template for target_model ---
        effective_system_prompt = (system_prompt.strip() if system_prompt else "") or get_system_prompt(
            target_model, screen_use
        )

        if minimal_llm:
            user_tail = ""
        else:
            user_tail = (
                sequence_instruction
                + no_person_instruction
                + multi_instruction
                + dialogue_instruction
                + explicit_instruction
                + lora_instruction
                + length_instruction
            )
        user_text = effective_input + user_tail
        if use_lm_studio and image is not None:
            try:
                data_url = _comfy_image_to_jpeg_data_url(image)
            except Exception as e:
                raise RuntimeError(
                    f"[LazyPrompt] Failed to encode IMAGE for LM Studio: {e}"
                ) from e
            messages = [
                {"role": "system", "content": effective_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ]
            print("[LazyPrompt] LM Studio request includes vision (multimodal user message).")
        else:
            messages = [
                {"role": "system", "content": effective_system_prompt},
                {"role": "user", "content": user_text},
            ]

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
            return (result, result, neg_prompt)

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

        return (result, result, neg_prompt)


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
