"""Extra user-message context: environments, duration, I2V hints (LazyPrompt)."""
from __future__ import annotations

import random
import re

from .environment_presets import ENVIRONMENT_PRESETS
from .system_prompts import has_audio, is_video_model


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
    elif "SDXL" in target_model or "Pony" in target_model or "SD 1.5" in target_model:
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


def compose_user_scene_input(
    effective_user: str,
    *,
    scene_context: str = "",
    character: str = "",
    target_model: str = "",
) -> str:
    """
    Build the core user-message body: optional scene_context and character layers,
    then user direction (scenario override or user_input). Always sent to the LLM,
    including minimal mode (None target + prompt_override / system_prompt).
    """
    user = (effective_user or "").strip()
    sc = (scene_context or "").strip()
    ch = (character or "").strip()
    if not sc and not ch:
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
    layers.append(
        "[USER DIRECTION — apply this as action, style, and mood over the above]\n"
        + user
    )
    return "\n\n".join(layers)


def build_prompt_augmentation(
    target_model: str,
    environment: str,
    frame_count: int,
    fps: float,
    seed: int,
    screenplay_mode: bool,
    has_scene_context: bool,
) -> str:
    """
    Text appended after the user's scene/instruction block.
    Does not include the raw user idea — the caller prepends that with LTX-style wrappers.
    """
    parts: list[str] = []

    if is_video_model(target_model):
        duration_sec = round(frame_count / max(fps, 1.0), 1)

        if "Wan" in target_model:
            parts.append(
                f"VIDEO LENGTH: {duration_sec}s ({frame_count} frames at {fps:g}fps). "
                f"Write 80-120 words. One clear shot progression with motion throughout.\n"
            )
        else:
            if screenplay_mode and "LTX" in target_model:
                if duration_sec <= 5:
                    arc = (
                        f"SHORT clip: {duration_sec}s ({frame_count} frames). "
                        f"Write the Characters block, Scene block, then 2–3 action beats."
                    )
                elif duration_sec <= 15:
                    arc = (
                        f"MEDIUM clip: {duration_sec}s ({frame_count} frames). "
                        f"Write the Characters block, Scene block, then 4–5 action beats."
                    )
                else:
                    arc = (
                        f"LONG clip: {duration_sec}s ({frame_count} frames). "
                        f"Write the Characters block, Scene block, then 6–8 action beats. "
                        f"Depth over breadth — stay in the same location, go deeper into "
                        f"the physical action and dialogue, do not introduce new locations."
                    )
            else:
                if duration_sec <= 5:
                    arc = (
                        f"SHORT clip: {duration_sec}s ({frame_count} frames). "
                        f"4–5 sentences. Stay inside the scene the user described — "
                        f"do not add locations, characters, or events they did not mention. "
                        f"One subject, one action, one camera move. Close on sound."
                    )
                elif duration_sec <= 15:
                    arc = (
                        f"MEDIUM clip: {duration_sec}s ({frame_count} frames). "
                        f"5–6 sentences. Stay inside the scene the user described. "
                        f"Go deeper — more texture, more physical detail, richer audio — "
                        f"do not introduce new locations or characters the user did not mention. "
                        f"Camera responds to each action. Close on sound."
                    )
                else:
                    arc = (
                        f"LONG clip: {duration_sec}s ({frame_count} frames). "
                        f"6–8 sentences. DEPTH NOT BREADTH — the extra length means more detail "
                        f"on the same subject in the same scene, not more locations, not more characters, "
                        f"not more events. Use it for: richer texture on the environment, "
                        f"more physical detail on the subject, layered audio, "
                        f"the camera moving closer or finding a new angle on the same action. "
                        f"Everything in the prompt must come directly from what the user described. "
                        f"Close on sound or silence."
                    )
            parts.append(f"VIDEO LENGTH: {arc}\n")

    if has_scene_context:
        if "Wan" in target_model:
            parts.append(
                "IMAGE / SCENE CONTEXT (I2V): A starting frame or detailed scene description was "
                "provided above. Treat it as the first frame — describe how existing elements "
                "should MOVE. Do NOT contradict the description. "
                "Lock face and identity: describe motion, camera, and light changes. "
                "Negative guidance: morphing, warping, face deformation, flickering.\n"
            )
        elif is_video_model(target_model):
            parts.append(
                "IMAGE / SCENE CONTEXT (I2V): Ground the prompt in exactly what the description "
                "or start frame implies — hair, skin, clothing, environment, lighting. "
                "Do not contradict it. The prompt describes this scene coming to life.\n"
            )
        else:
            parts.append(
                "REFERENCE CONTEXT (I2I): Use the scene description as grounding for subject, "
                "style, lighting, and composition. Evolve or match it as appropriate for the target model.\n"
            )

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

    if has_audio(target_model):
        parts.append(
            "AUDIO: Video model generates audio. Include rich layered audio description: "
            "foreground action + mid-ground ambient + background atmosphere. "
            "Breathing and fabric are sound sources. Final sentence should land on sound.\n"
        )

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
