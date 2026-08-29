"""Extra user-message context: environments (LazyPrompt).

Duration, people, timeline, and content-tone rules live in Model_Skills/*.md
(***VideoLength*** slot + SCENE POLICY). SAS ``[video_length]`` in the user
text is kept so the model can size beats. This module composes user-message
layers and optional environment-preset facts.
"""
from __future__ import annotations

import random
import re

from .environment_presets import ENVIRONMENT_PRESETS
from .system_prompts import (
    is_tag_style_model,
    is_video_model,
)


def _character_preface(character: str, target_model: str) -> str:
    """Subject/character block prepended to the LLM user message (always, including minimal mode)."""
    ch = character.strip()
    if not ch:
        return ""
    if is_video_model(target_model):
        hint = (
            "use this physical description exactly — anchor identity early in the prompt; "
            "do not invent or contradict it"
        )
    elif is_tag_style_model(target_model):
        hint = (
            "convert these descriptors into appropriate tags for the target format; "
            "do not drop or replace them"
        )
    else:
        hint = (
            "use this physical description exactly in your prompt; "
            "do not invent or contradict it"
        )
    return f"[SUBJECT / CHARACTER — {hint}]\n{ch}"


_SAS_VIDEO_LENGTH_RE = re.compile(
    r"\[video_length\][^\n]*(?:\n\s*(\d+(?:\.\d+)?)\s*s\s*)?",
    re.IGNORECASE,
)


def parse_sas_video_length_sec(text: str) -> float | None:
    """Seconds from a SAS ``[video_length]`` / ``12s`` block, if present."""
    m = _SAS_VIDEO_LENGTH_RE.search(text or "")
    if not m or not m.group(1):
        return None
    try:
        sec = float(m.group(1))
    except ValueError:
        return None
    return sec if sec > 0 else None


def compose_user_scene_input(
    effective_user: str,
    *,
    scene_context: str = "",
    character: str = "",
    target_model: str = "",
    user_instructions: str = "",
) -> str:
    """
    Build the core user-message body: optional scene_context, character,
    user_instructions, then user direction (scenario override or user_input).
    Always sent to the LLM, including minimal mode.
    SAS ``[video_length]`` stays in the user text so the model can size beats.
    """
    user = (effective_user or "").strip()
    sc = (scene_context or "").strip()
    ch = (character or "").strip()
    instr = (user_instructions or "").strip()

    if not sc and not ch and not instr:
        return user

    layers: list[str] = []
    if sc:
        layers.append(
            "[SCENE CONTEXT FROM IMAGE — use this as the authoritative description "
            "of the subject and setting; do not invent or contradict it]\n"
            + sc
        )
    if ch:
        preface = _character_preface(ch, target_model)
        if preface:
            layers.append(preface)
    if instr:
        layers.append(
            "[USER INSTRUCTIONS — mandatory for this run. "
            "Named people, places, actions, shot times, and quoted dialogue are locked facts. "
            "Write that scene. Do not treat the scene as missing or empty.]\n"
            + instr
        )
    if user:
        layers.append(
            "[USER DIRECTION — apply this as action, style, and mood over the above]\n"
            + user
        )
    return "\n\n".join(layers) if layers else user


def build_prompt_augmentation(
    target_model: str,
    environment: str,
    seed: int,
) -> str:
    """Optional environment-preset facts appended after the user's scene block."""
    parts: list[str] = []

    env_data = ENVIRONMENT_PRESETS.get(environment)
    if env_data == "RANDOM":
        valid_envs = [v for v in ENVIRONMENT_PRESETS.values() if v is not None and v != "RANDOM"]
        rng = random.Random(seed if seed != 0 else None)
        env_data = rng.choice(valid_envs)

    if env_data and isinstance(env_data, tuple) and len(env_data) >= 3:
        location, lighting, sound = env_data
        parts.append("ENVIRONMENT:")
        parts.append(f"  Location: {location}")
        parts.append(f"  Lighting: {lighting}")
        if is_video_model(target_model):
            parts.append(f"  Sound: {sound}")
        parts.append("")

    if parts:
        return "\n".join(parts).rstrip() + "\n"
    return ""


def split_positive_negative_block(text: str) -> tuple[str, str]:
    """
    SDXL / Pony / SD1.5 templates often emit POSITIVE: and NEGATIVE: sections.
    Returns (positive_only, negative_only). If no NEGATIVE: line, second value is "".
    """
    t = text.strip()
    neg_match = re.search(r"(?i)\s*negative\s*:", t)
    if not neg_match:
        return t, ""
    pos = t[: neg_match.start()].strip()
    neg = t[neg_match.end() :].strip()
    pos = re.sub(r"(?i)^\s*positive\s*:\s*", "", pos, flags=re.MULTILINE).strip()
    return pos, neg
