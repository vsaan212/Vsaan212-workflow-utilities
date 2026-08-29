"""Target-model system prompts and router (LazyPrompt).

Default skill templates load from ``Model_Skills/*.md`` in this folder.
Edit those Markdown files to customize prompts; add a new ``.md`` for a new skill.
Restart ComfyUI or press **R** (refresh) to reload.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Dropdown label for “no template — empty system unless you use override”
TARGET_NONE_LABEL = "\u23f9 None — empty default system prompt (override optional)"

_SKILLS_DIR = Path(__file__).with_name("Model_Skills")
_ICON_BY_TYPE = {
    "video": "\U0001f3ac",  # 🎬
    "image": "\U0001f5bc",  # 🖼
    "sound": "\U0001f50a",  # 🔊
}

_VIDEO_LENGTH_BLOCK_RE = re.compile(
    r"\*\*\*VideoLength\*\*\*.*?\*\*\*VideoLengthEnd\*\*\*",
    re.DOTALL | re.IGNORECASE,
)
_VIDEO_LENGTH_SECTION_RE = re.compile(
    r"(?:"
    r"(?:^|\n)---\s*\nCLIP DURATION SLOT:.*?"
    r")?\*\*\*VideoLength\*\*\*.*?\*\*\*VideoLengthEnd\*\*\*",
    re.DOTALL | re.IGNORECASE,
)
_USER_PROMPT_BLOCK_RE = re.compile(
    r"\*\*\*UserPrompt\*\*\*.*?\*\*\*UserPromptEnd\*\*\*",
    re.DOTALL | re.IGNORECASE,
)
# Full section including the instructional preamble above the markers (empty → omit entirely)
_USER_PROMPT_SECTION_RE = re.compile(
    r"(?:"
    r"(?:^|\n)---\s*\nUSER INSTRUCTIONS BLOCK:.*?"
    r")?\*\*\*UserPrompt\*\*\*.*?\*\*\*UserPromptEnd\*\*\*",
    re.DOTALL | re.IGNORECASE,
)

_cache_mtime_key: tuple[float, ...] | None = None
_skills_by_label: dict[str, "ModelSkill"] | None = None
_dropdown_labels: list[str] | None = None


def is_none_target(target_model: str) -> bool:
    t = (target_model or "").strip()
    return t == TARGET_NONE_LABEL or t.startswith("\u23f9 None —")


@dataclass(frozen=True)
class ModelSkill:
    """One skill loaded from Model_Skills/*.md."""

    stem: str
    path: Path
    model_type: str
    model_name: str
    media_type: str
    is_video: bool
    has_audio: bool
    prompt: str
    label: str


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_header_and_prompt(text: str) -> dict[str, str]:
    """
    Parse ===Header=== ... Prompt: <body>.

    Returns keys: model_type, model_name, media_type, is_video, has_audio, prompt.
    """
    raw = text.lstrip("\ufeff")
    # Allow optional leading whitespace / BOM
    header_match = re.search(
        r"(?is)===Header===\s*(.*?)\n\s*Prompt\s*:\s*\n?(.*)\Z",
        raw,
    )
    if not header_match:
        raise ValueError("missing ===Header=== / Prompt: section")

    meta_block, prompt_body = header_match.group(1), header_match.group(2)
    fields: dict[str, str] = {}
    for line in meta_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fields[key.strip().lower()] = val.strip()

    return {
        "model_type": fields.get("model type", "Image"),
        "model_name": fields.get("model name", ""),
        "media_type": fields.get("media type", ""),
        "is_video": fields.get("is video", "false"),
        "has_audio": fields.get("has audio", "false"),
        "prompt": prompt_body.strip(),
    }


def _icon_for_type(model_type: str) -> str:
    return _ICON_BY_TYPE.get((model_type or "").strip().lower(), "\u2728")


def _build_label(model_type: str, model_name: str, media_type: str) -> str:
    icon = _icon_for_type(model_type)
    name = (model_name or "").strip() or "Unnamed"
    media = (media_type or "").strip()
    if media:
        return f"{icon} {name}  — {media}"
    return f"{icon} {name}"


def _folder_mtime_key(folder: Path) -> tuple[float, ...]:
    if not folder.is_dir():
        return ()
    times: list[float] = []
    try:
        times.append(folder.stat().st_mtime)
    except OSError:
        pass
    for path in sorted(folder.glob("*.md")):
        try:
            times.append(path.stat().st_mtime)
        except OSError:
            continue
    return tuple(times)


def load_model_skills(*, force: bool = False) -> dict[str, ModelSkill]:
    """
    Scan Model_Skills/*.md and return skills keyed by dropdown label.
    Reloads when any skill file (or the folder) changes.
    """
    global _cache_mtime_key, _skills_by_label, _dropdown_labels

    key = _folder_mtime_key(_SKILLS_DIR)
    if (
        not force
        and _skills_by_label is not None
        and _dropdown_labels is not None
        and _cache_mtime_key == key
    ):
        return _skills_by_label

    skills: dict[str, ModelSkill] = {}
    labels: list[str] = [TARGET_NONE_LABEL]

    if not _SKILLS_DIR.is_dir():
        print(f"[LazyPrompt] Model_Skills folder missing at {_SKILLS_DIR}")
        _skills_by_label = skills
        _dropdown_labels = labels
        _cache_mtime_key = key
        return skills

    for path in sorted(_SKILLS_DIR.glob("*.md"), key=lambda p: p.name.lower()):
        try:
            text = path.read_text(encoding="utf-8")
            parsed = _parse_header_and_prompt(text)
        except (OSError, ValueError) as e:
            print(f"[LazyPrompt] Skipping skill {path.name}: {e}")
            continue

        model_name = parsed["model_name"]
        if not model_name:
            print(f"[LazyPrompt] Skipping skill {path.name}: empty Model Name")
            continue
        if not parsed["prompt"]:
            print(f"[LazyPrompt] Warning: skill {path.name} has empty Prompt body")

        label = _build_label(
            parsed["model_type"], model_name, parsed["media_type"]
        )
        if label in skills:
            print(
                f"[LazyPrompt] Duplicate dropdown label {label!r} "
                f"from {path.name}; keeping first, skipping duplicate."
            )
            continue

        skill = ModelSkill(
            stem=path.stem,
            path=path,
            model_type=parsed["model_type"],
            model_name=model_name,
            media_type=parsed["media_type"],
            is_video=_truthy(parsed["is_video"]),
            has_audio=_truthy(parsed["has_audio"]),
            prompt=parsed["prompt"],
            label=label,
        )
        skills[label] = skill
        labels.append(label)

    _skills_by_label = skills
    _dropdown_labels = labels
    _cache_mtime_key = key
    print(
        f"[LazyPrompt] Loaded {len(skills)} model skill(s) from {_SKILLS_DIR.name}/"
    )
    return skills


def get_target_model_choices() -> list[str]:
    """Dropdown labels including None. Refreshes from disk when files change."""
    load_model_skills()
    return list(_dropdown_labels or [TARGET_NONE_LABEL])


def get_default_target_model() -> str:
    choices = get_target_model_choices()
    # Prefer base LTX 2.3 (not Screenplay / Dialog variants) when present
    for label in choices:
        if is_none_target(label):
            continue
        if (
            "LTX 2.3" in label
            and "Screenplay" not in label
            and "Dialog" not in label
        ):
            return label
    for label in choices:
        if not is_none_target(label):
            return label
    return TARGET_NONE_LABEL


def get_skill(target_model: str) -> ModelSkill | None:
    if is_none_target(target_model):
        return None
    skills = load_model_skills()
    if target_model in skills:
        return skills[target_model]

    needle = (target_model or "").strip().lower()
    for label, s in skills.items():
        if label.lower() == needle:
            return s

    # Legacy labels: prefer longest Model Name contained in the saved string
    # (so "LTX 2.3 Dialog" wins over "LTX 2.3").
    best: ModelSkill | None = None
    best_len = -1
    for s in skills.values():
        name = s.model_name.lower().strip()
        if name and name in needle and len(name) > best_len:
            best = s
            best_len = len(name)
    return best


def get_system_prompt(target_model: str) -> str:
    skill = get_skill(target_model)
    if not skill:
        if not is_none_target(target_model):
            print(
                f"[LazyPrompt] No Model_Skills entry for {target_model!r} — "
                "system message empty unless override is set."
            )
        return ""
    return (skill.prompt or "").strip()


def is_video_model(target_model: str) -> bool:
    skill = get_skill(target_model)
    if skill is not None:
        return skill.is_video
    if is_none_target(target_model):
        return False
    # Fallback for unknown legacy labels
    t = target_model or ""
    return "LTX" in t or "Wan" in t


def has_audio(target_model: str) -> bool:
    skill = get_skill(target_model)
    if skill is not None:
        return skill.has_audio
    if is_none_target(target_model):
        return False
    return "LTX" in (target_model or "")


def is_screenplay_skill(target_model: str) -> bool:
    skill = get_skill(target_model)
    if skill is None:
        return False
    blob = f"{skill.model_name} {skill.media_type}".lower()
    return "screenplay" in blob


def is_tag_style_model(target_model: str) -> bool:
    skill = get_skill(target_model)
    blob = ""
    if skill is not None:
        blob = f"{skill.model_name} {skill.media_type}".lower()
    else:
        blob = (target_model or "").lower()
    return any(x in blob for x in ("sdxl", "pony", "sd 1.5", "booru"))


def is_wan_skill(target_model: str) -> bool:
    skill = get_skill(target_model)
    if skill is not None:
        return "wan" in skill.model_name.lower()
    return "Wan" in (target_model or "")


def apply_video_length_slot(system_prompt: str, video_length_sec: float) -> str:
    """Fill or strip ***VideoLength*** … ***VideoLengthEnd*** in a skill template.

    Video runs with duration > 0 write e.g. ``8s`` between the markers.
    Image runs, zero duration, or missing markers: the whole slot section is removed.
    """
    text = system_prompt or ""
    if not _VIDEO_LENGTH_BLOCK_RE.search(text):
        return text
    duration = float(video_length_sec or 0.0)
    if duration <= 0:
        cleaned = _VIDEO_LENGTH_SECTION_RE.sub("", text)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    dur = f"{round(duration, 2):g}s"
    replacement = f"***VideoLength***\n{dur}\n***VideoLengthEnd***"
    return _VIDEO_LENGTH_BLOCK_RE.sub(replacement, text, count=1)


def apply_skill_runtime(
    system_prompt: str,
    *,
    user_instructions: str = "",
    video_length_sec: float = 0.0,
) -> str:
    """Apply all skill-file runtime slots (UserPrompt, VideoLength)."""
    text = apply_user_prompt_injection(system_prompt, user_instructions)
    return apply_video_length_slot(text, video_length_sec)


def apply_user_prompt_injection(system_prompt: str, user_instructions: str) -> str:
    """
    Inject optional user instructions into ***UserPrompt*** … ***UserPromptEnd***.

    - Empty instructions: remove the entire marker block (pass nothing).
    - Non-empty: place the text between the markers (markers kept).
    - If markers are missing and instructions are non-empty: append a standard block.
    """
    text = system_prompt or ""
    instructions = (user_instructions or "").strip()

    if not instructions:
        cleaned = _USER_PROMPT_SECTION_RE.sub("", text)
        # Tidy leftover blank lines from removal
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    replacement = (
        f"***UserPrompt***\n{instructions}\n***UserPromptEnd***"
    )
    if _USER_PROMPT_BLOCK_RE.search(text):
        return _USER_PROMPT_BLOCK_RE.sub(replacement, text, count=1)

    print(
        "[LazyPrompt] user_instructions set but ***UserPrompt*** markers missing; "
        "appending instruction block."
    )
    return (
        text.rstrip()
        + "\n\n---\nUSER INSTRUCTIONS (mandatory for this run):\n"
        + replacement
        + "\n"
    )


SKILLS_HINT = (
    "Skills load from lazyprompt/Model_Skills/*.md "
    "(restart ComfyUI or press R after edits)."
)

# Back-compat alias used by older docs / imports
JSON_PROMPTS_HINT = SKILLS_HINT

# Populated at import for callers that still read these constants;
# INPUT_TYPES uses get_target_model_choices() / get_default_target_model() for freshness.
TARGET_MODELS = get_target_model_choices()
TARGET_MODEL_DEFAULT = get_default_target_model()
