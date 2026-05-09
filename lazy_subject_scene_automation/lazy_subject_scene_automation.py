"""
Lazy Subject + Scene Automation — combines subject/scenario file parsing,
optional LoRA bypass behavior, and prompt assembly for Wan 2.1 / 2.2 style stacks.

Tagged (v2) files use unified slot names: LoraHighA/LoraLowA through LoraHighC/LoraLowC
in both subject and scenario files; older SubjectLora* / ScenarioLora* tags remain supported.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from comfy import model_management
from nodes import LoraLoader

ApplySlot = Tuple[str, float, float]  # path, strength_model, strength_clip

# v2 tagged minimal stem: no LoRAs, empty description (used for shipped none.txt + seeding).
_LAZY_V2_STEM_TEMPLATE = (
    "[LoraHighA]\n"
    "Bypass\n"
    "[LoraLowA]\n"
    "bypass\n"
    "[desciption]\n"
)


# WebSocket event: server tells clients to refresh preset dropdown after save.
LAZY_PRESET_WS_EVENT = "vsaan212.lazy_subject_scene.presets"

# Default scenario-side tagged template (v2 slot names). Stored in preset JSON as `scenario_template`.
DEFAULT_SCENARIO_TEMPLATE = """[LoraHighA][1.0][1.0]
bypass
[LoraLowA][1.0][1.0]
bypass
[LoraHighB][1.0][1.0]
bypass
[LoraLowB][1.0][1.0]
bypass
[LoraHighC][1.0][1.0]
bypass
[LoraLowC][1.0][1.0]
bypass
[KeywordA]
[KeywordB]
[KeywordC]
[desciption]
"""


def _normalize_rel_no_ext(rel: str) -> str:
    return (rel or "").strip().replace("\\", "/").strip("/")


def _is_safe_rel_under_root(
    root: str, rel_no_ext: str, file_suffix: str = ".txt"
) -> bool:
    """Reject path traversal; rel_no_ext is relative path without the given suffix."""
    rel = _normalize_rel_no_ext(rel_no_ext)
    if not rel or rel == "none":
        return True
    if ".." in rel.split("/"):
        return False
    candidate = os.path.normpath(
        os.path.join(os.path.abspath(root), rel + file_suffix)
    )
    root_abs = os.path.abspath(root)
    try:
        common = os.path.commonpath([candidate, root_abs])
    except ValueError:
        return False
    return common == root_abs


def _read_txt_under_root(root: str, rel_no_ext: str) -> Tuple[str, Optional[str]]:
    rel = _normalize_rel_no_ext(rel_no_ext)
    if not rel or rel == "none":
        return "", None
    if not _is_safe_rel_under_root(root, rel):
        return "", "invalid path"
    path = os.path.join(root, rel + ".txt")
    if not os.path.isfile(path):
        return "", f"not found: {rel}.txt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None
    except OSError as e:
        return "", str(e)


def _ensure_lazy_seed_txt_files() -> None:
    """
    If SubjectFiles/ScenarioFiles are missing default .txt files, create them.
    Called when dropdown lists refresh so empty installs still get `none` and the bypass example.
    Does not overwrite existing files.
    """
    pkg_root = os.path.dirname(__file__)
    for sub in ("SubjectFiles", "ScenarioFiles"):
        d = os.path.join(pkg_root, sub)
        os.makedirs(d, exist_ok=True)
        for fname in ("none.txt", "Bypass and format example.txt"):
            path = os.path.join(d, fname)
            if not os.path.isfile(path):
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(_LAZY_V2_STEM_TEMPLATE)


def _norm_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (tag or "").lower())


def _bypass_path(body: str) -> bool:
    s = (body or "").strip().strip('"').strip("'")
    return not s or s.lower() == "bypass"


def _parse_float(s: Optional[str], default: Optional[float] = None) -> Optional[float]:
    if s is None:
        return default
    t = str(s).strip()
    if not t:
        return default
    try:
        return float(t)
    except ValueError:
        return default


def _split_v1_sections(content: str) -> List[str]:
    text = content.strip().replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"\n\s*#\s*\n", text)
    return [p.strip() for p in parts]


def _is_tagged_format(content: str) -> bool:
    for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = line.strip()
        if s and s.startswith("["):
            return True
    return False


def _parse_tagged_blocks(content: str) -> Dict[str, Tuple[str, float, float]]:
    """
    Parse [Tag][model_strength][clip_strength] lines followed by body until next tag.
    Missing strengths default to 1.0. Returns map norm_tag -> (body, sm, sc).
    Last occurrence wins for duplicate tags.
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: Dict[str, Tuple[str, float, float]] = {}
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if not stripped.startswith("["):
            i += 1
            continue

        groups = re.findall(r"\[([^\]]*)\]", stripped)
        if not groups:
            i += 1
            continue

        tag_raw = groups[0].strip()
        sm = _parse_float(groups[1] if len(groups) > 1 else None, 1.0)
        sc = _parse_float(groups[2] if len(groups) > 2 else None, 1.0)
        if sm is None:
            sm = 1.0
        if sc is None:
            sc = 1.0

        i += 1
        body_lines: List[str] = []
        while i < n:
            nxt = lines[i]
            if nxt.strip().startswith("["):
                break
            body_lines.append(nxt)
            i += 1
        body = "\n".join(body_lines).strip()
        blocks[_norm_tag(tag_raw)] = (body, float(sm), float(sc))

    return blocks


def _slot_from_block(
    body: str, sm: float, sc: float
) -> Optional[ApplySlot]:
    if _bypass_path(body):
        return None
    return (body.strip().strip('"').strip("'"), sm, sc)


def _block_first(
    blocks: Dict[str, Tuple[str, float, float]], *tag_names: str
) -> Optional[Tuple[str, float, float]]:
    """First matching tag wins; supports deprecated aliases for older files."""
    for name in tag_names:
        b = blocks.get(_norm_tag(name))
        if b is not None:
            return b
    return None


def _append_optional_pair(
    blocks: Dict[str, Tuple[str, float, float]],
    high_key: str,
    low_key: str,
    high_stack: List[ApplySlot],
    low_stack: List[ApplySlot],
) -> None:
    hk = _norm_tag(high_key)
    lk = _norm_tag(low_key)
    hb = blocks.get(hk)
    lb = blocks.get(lk)

    sh = _slot_from_block(*hb) if hb else None
    sl = _slot_from_block(*lb) if lb else None

    if sh and sl:
        high_stack.append(sh)
        low_stack.append(sl)
    elif sh and not sl:
        p, sm, cm = sh
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))
    elif sl and not sh:
        p, sm, cm = sl
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))


def _append_optional_slot(
    blocks: Dict[str, Tuple[str, float, float]],
    high_stack: List[ApplySlot],
    low_stack: List[ApplySlot],
    *alias_pairs: Tuple[str, str],
) -> None:
    """Apply the first (high, low) tag pair that appears in the file (deprecated aliases last)."""
    for high_key, low_key in alias_pairs:
        hk = _norm_tag(high_key)
        lk = _norm_tag(low_key)
        if blocks.get(hk) is not None or blocks.get(lk) is not None:
            _append_optional_pair(blocks, high_key, low_key, high_stack, low_stack)
            return


def _append_primary_subject(
    blocks: Dict[str, Tuple[str, float, float]],
    high_stack: List[ApplySlot],
    low_stack: List[ApplySlot],
) -> None:
    shb = _block_first(blocks, "LoraHighA", "SubjectLoraHigh")
    slb = _block_first(blocks, "LoraLowA", "SubjectLoraLow")
    sh = _slot_from_block(*shb) if shb else None
    sl = _slot_from_block(*slb) if slb else None

    if sh and sl:
        high_stack.append(sh)
        low_stack.append(sl)
    elif sh and not sl:
        p, sm, cm = sh
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))
    elif sl and not sh:
        p, sm, cm = sl
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))


def _append_primary_scenario(
    blocks: Dict[str, Tuple[str, float, float]],
    high_stack: List[ApplySlot],
    low_stack: List[ApplySlot],
) -> None:
    shb = _block_first(blocks, "LoraHighA", "ScenarioLoraHigh")
    slb = _block_first(blocks, "LoraLowA", "ScenarioLoraLow")
    sh = _slot_from_block(*shb) if shb else None
    sl = _slot_from_block(*slb) if slb else None

    if sh and sl:
        high_stack.append(sh)
        low_stack.append(sl)
    elif sh and not sl:
        p, sm, cm = sh
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))
    elif sl and not sh:
        p, sm, cm = sl
        high_stack.append((p, sm, cm))
        low_stack.append((p, sm, 1.0))


def _subject_stacks_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> Tuple[List[ApplySlot], List[ApplySlot]]:
    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    _append_primary_subject(blocks, high, low)
    _append_optional_slot(
        blocks,
        high,
        low,
        ("LoraHighB", "LoraLowB"),
        ("OptionalLoraAHigh", "OptionalLoraAlow"),
    )
    _append_optional_slot(
        blocks,
        high,
        low,
        ("LoraHighC", "LoraLowC"),
        ("OptionalLoraBHigh", "OptionalLoraBlow"),
    )
    return high, low


def _scenario_stacks_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> Tuple[List[ApplySlot], List[ApplySlot]]:
    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    _append_primary_scenario(blocks, high, low)
    _append_optional_slot(
        blocks,
        high,
        low,
        ("LoraHighB", "LoraLowB"),
        ("OptionalScenarioALoraHigh", "OptionalScenarioALoraLow"),
    )
    _append_optional_slot(
        blocks,
        high,
        low,
        ("LoraHighC", "LoraLowC"),
        ("OptionalScenarioBLoraHigh", "OptionalScenarioBLoraLow"),
    )
    return high, low


def _keywords_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> List[str]:
    out: List[str] = []
    for key in ("keyworda", "keywordb", "keywordc"):
        b = blocks.get(key)
        if not b:
            continue
        text = (b[0] or "").strip()
        if text and not _bypass_path(text):
            out.append(text)
    return out


def _description_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> str:
    for alias in ("description", "desciption"):
        b = blocks.get(_norm_tag(alias))
        if b:
            return (b[0] or "").strip()
    return ""


def parse_subject_text(content: str) -> Tuple[List[ApplySlot], List[ApplySlot], str, List[str]]:
    content = (content or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if not content:
        return [], [], "", []

    if _is_tagged_format(content):
        blocks = _parse_tagged_blocks(content)
        hi, lo = _subject_stacks_from_blocks(blocks)
        desc = _description_from_blocks(blocks)
        kws = _keywords_from_blocks(blocks)
        return hi, lo, desc, kws

    parts = _split_v1_sections(content)
    if not parts:
        return [], [], "", []

    desc = parts[-1] if len(parts) > 1 else (parts[0] if len(parts) == 1 else "")
    path_parts = parts[:-1] if len(parts) > 1 else []

    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    if len(path_parts) >= 2:
        for p in path_parts[:2]:
            if _bypass_path(p):
                continue
            high.append((p.strip().strip('"').strip("'"), 1.0, 1.0))
            low.append((p.strip().strip('"').strip("'"), 1.0, 1.0))
    elif len(path_parts) == 1:
        p = path_parts[0]
        if not _bypass_path(p):
            q = p.strip().strip('"').strip("'")
            high.append((q, 1.0, 1.0))
            low.append((q, 1.0, 1.0))

    return high, low, desc, []


def parse_scenario_text(content: str) -> Tuple[List[ApplySlot], List[ApplySlot], str, List[str]]:
    content = (content or "").strip().replace("\r\n", "\n").replace("\r", "\n")
    if not content:
        return [], [], "", []

    if _is_tagged_format(content):
        blocks = _parse_tagged_blocks(content)
        hi, lo = _scenario_stacks_from_blocks(blocks)
        desc = _description_from_blocks(blocks)
        kws = _keywords_from_blocks(blocks)
        return hi, lo, desc, kws

    parts = _split_v1_sections(content)
    if not parts:
        return [], [], "", []

    desc = parts[-1] if len(parts) > 1 else (parts[0] if len(parts) == 1 else "")
    path_parts = parts[:-1] if len(parts) > 1 else []

    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    if len(path_parts) >= 2:
        p0, p1 = path_parts[0], path_parts[1]
        if not _bypass_path(p0):
            high.append((p0.strip().strip('"').strip("'"), 1.0, 1.0))
        if not _bypass_path(p1):
            low.append((p1.strip().strip('"').strip("'"), 1.0, 1.0))
    elif len(path_parts) == 1:
        p = path_parts[0]
        if not _bypass_path(p):
            q = p.strip().strip('"').strip("'")
            high.append((q, 1.0, 1.0))
            low.append((q, 1.0, 1.0))

    return high, low, desc, []


def _merge_stacks(
    subj: List[ApplySlot], scen: List[ApplySlot]
) -> List[ApplySlot]:
    return list(subj) + list(scen)


def _resolve_lora_name(cmd: str) -> str:
    path = cmd.strip().strip('"').strip("'")
    if os.path.exists(path):
        lora_dir = os.path.dirname(os.path.abspath(path))
        model_management.lora_paths.add(lora_dir)
        return os.path.basename(path)
    return path


def _apply_stack(model, clip, stack: List[ApplySlot]):
    loader = LoraLoader()
    for path, sm, cm in stack:
        if _bypass_path(path):
            continue
        lora_name = _resolve_lora_name(path)
        if not lora_name or lora_name.lower() == "bypass":
            continue
        model, clip = loader.load_lora(model, clip, lora_name, sm, cm)
    return model, clip


def _format_keywords(subject_kws: List[str], scenario_kws: List[str]) -> str:
    parts = [k for k in subject_kws if k] + [k for k in scenario_kws if k]
    if not parts:
        return ""
    return ", ".join(parts) + ", "


def _build_prompt(prepend: str, post: str, subj_desc: str, scen_desc: str) -> str:
    """
    Readability for preview nodes:
    - newline after prepend when present
    - blank line before post_text when something precedes it
    - blank line before scenario description when both subject-side and scenario exist
    """
    pre = prepend or ""
    sd = (subj_desc or "").strip()
    po = post or ""
    scen = (scen_desc or "").strip()
    po_stripped = po.strip()

    chunks: List[str] = []
    if pre.strip():
        chunks.append(pre.rstrip() + "\n")
    if sd:
        chunks.append(sd)
    if po_stripped:
        if chunks:
            prior = "".join(chunks)
            # One blank line above post: if prior already ends with \n (e.g. after prepend), add one \n; else \n\n
            sep = "\n" + po_stripped if prior.endswith("\n") else "\n\n" + po_stripped
            chunks.append(sep)
        else:
            chunks.append(po_stripped)

    subject_side = "".join(chunks)

    if subject_side.strip() and scen:
        return subject_side.rstrip("\n") + "\n\n" + scen
    if scen and not subject_side.strip():
        return scen
    return subject_side


class LazySubjectSceneAutomation:
    """
    Loads subject + scenario .txt files (v1 # format or v2 tagged format), applies
    LoRA stacks with optional bypass, and assembles prompt + keywords.
    Files live under this package's SubjectFiles/ and ScenarioFiles/.
    On list refresh, missing `none.txt` or `Bypass and format example.txt` in either
    folder are created from the current v2 template (existing files are never overwritten).
    """

    subjects_relpaths: List[str] = []
    scenarios_relpaths: List[str] = []
    presets_relpaths: List[str] = []
    subjects_root: str = ""
    scenarios_root: str = ""
    presets_root: str = ""

    @classmethod
    def refresh_subjects_list(cls) -> None:
        _ensure_lazy_seed_txt_files()
        subject_dir = os.path.join(os.path.dirname(__file__), "SubjectFiles")
        cls.subjects_root = subject_dir
        if not os.path.exists(subject_dir):
            os.makedirs(subject_dir, exist_ok=True)
        subjects: List[str] = []
        for root, _, files in os.walk(subject_dir):
            for f in files:
                if f.lower().endswith(".txt"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, subject_dir).replace("\\", "/")
                    subjects.append(rel_path[:-4])
        cls.subjects_relpaths = subjects

    @classmethod
    def refresh_scenarios_list(cls) -> None:
        _ensure_lazy_seed_txt_files()
        scenario_dir = os.path.join(os.path.dirname(__file__), "ScenarioFiles")
        cls.scenarios_root = scenario_dir
        if not os.path.exists(scenario_dir):
            os.makedirs(scenario_dir, exist_ok=True)
        scenarios: List[str] = []
        for root, _, files in os.walk(scenario_dir):
            for f in files:
                if f.lower().endswith(".txt"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, scenario_dir).replace("\\", "/")
                    scenarios.append(rel_path[:-4])
        cls.scenarios_relpaths = scenarios

    @classmethod
    def refresh_presets_list(cls) -> None:
        preset_dir = os.path.join(os.path.dirname(__file__), "Presets")
        cls.presets_root = preset_dir
        os.makedirs(preset_dir, exist_ok=True)
        presets: List[str] = []
        for root, _, files in os.walk(preset_dir):
            for f in files:
                if f.lower().endswith(".json"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, preset_dir).replace("\\", "/")
                    presets.append(rel_path[:-5])
        cls.presets_relpaths = presets

    @classmethod
    def api_read_pair(cls, subject: str, scenario: str) -> Dict[str, Any]:
        cls.refresh_subjects_list()
        cls.refresh_scenarios_list()
        subj_text, subj_err = _read_txt_under_root(cls.subjects_root, subject)
        scen_text, scen_err = _read_txt_under_root(cls.scenarios_root, scenario)
        return {
            "subject_text": subj_text,
            "scenario_text": scen_text,
            "subject_error": subj_err,
            "scenario_error": scen_err,
            "error": subj_err or scen_err,
        }

    @classmethod
    def api_list_presets(cls) -> Dict[str, Any]:
        cls.refresh_presets_list()
        return {"presets": sorted(cls.presets_relpaths, key=lambda s: s.lower())}

    @classmethod
    def api_load_preset(cls, preset: str) -> Dict[str, Any]:
        import json

        cls.refresh_presets_list()
        rel = _normalize_rel_no_ext(preset)
        if not rel or rel == "(none)":
            return {"error": "no preset selected"}
        if not _is_safe_rel_under_root(cls.presets_root, rel, ".json"):
            return {"error": "invalid preset path"}
        path = os.path.join(cls.presets_root, rel + ".json")
        if not os.path.isfile(path):
            return {"error": f"preset not found: {rel}.json"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return {"error": str(e)}
        if not isinstance(data, dict):
            return {"error": "preset must be a JSON object"}
        subj = str(data.get("subject", "") or "")
        scen = str(data.get("scenario", "") or "")
        pair = cls.api_read_pair(subj, scen)
        out = {
            "subject": subj,
            "scenario": scen,
            "prepend_text": str(data.get("prepend_text", "") or ""),
            "post_text": str(data.get("post_text", "") or ""),
            "pass_subject_to_main_prompt": bool(
                data.get("pass_subject_to_main_prompt", True)
            ),
            "scenario_template": str(
                data.get("scenario_template", "") or DEFAULT_SCENARIO_TEMPLATE
            ),
            "subject_text": pair["subject_text"],
            "scenario_text": pair["scenario_text"],
            "error": pair.get("error"),
        }
        return out

    @classmethod
    def api_save_preset(cls, body: Dict[str, Any]) -> Dict[str, Any]:
        import json

        cls.refresh_presets_list()
        name = _normalize_rel_no_ext(str(body.get("name", "") or ""))
        if not name or name == "(none)":
            return {"error": "missing or invalid preset name"}
        if not _is_safe_rel_under_root(cls.presets_root, name, ".json"):
            return {"error": "invalid preset name or path"}
        path_abs = os.path.normpath(
            os.path.join(os.path.abspath(cls.presets_root), name + ".json")
        )
        payload = {
            "subject": str(body.get("subject", "") or ""),
            "scenario": str(body.get("scenario", "") or ""),
            "prepend_text": str(body.get("prepend_text", "") or ""),
            "post_text": str(body.get("post_text", "") or ""),
            "pass_subject_to_main_prompt": bool(
                body.get("pass_subject_to_main_prompt", True)
            ),
            "scenario_template": str(
                body.get("scenario_template", "") or DEFAULT_SCENARIO_TEMPLATE
            ),
        }
        os.makedirs(os.path.dirname(path_abs), exist_ok=True)
        try:
            with open(path_abs, "w", encoding="utf-8", newline="\n") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except OSError as e:
            return {"error": str(e)}
        root_abs = os.path.abspath(cls.presets_root)
        return {
            "ok": True,
            "path": os.path.relpath(path_abs, root_abs).replace("\\", "/"),
        }

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        cls.refresh_subjects_list()
        cls.refresh_scenarios_list()
        cls.refresh_presets_list()
        subj_choices = sorted(cls.subjects_relpaths, key=lambda s: s.lower())
        scen_choices = sorted(cls.scenarios_relpaths, key=lambda s: s.lower())
        preset_choices = ["(none)"] + sorted(
            cls.presets_relpaths, key=lambda s: s.lower()
        )
        if not subj_choices:
            subj_choices = ["none"]
        if not scen_choices:
            scen_choices = ["none"]
        return {
            "required": {
                "model_high": ("MODEL",),
                "model_low": ("MODEL",),
                "clip_high": ("CLIP",),
                "clip_low": ("CLIP",),
                "subject": (subj_choices,),
                "scenario": (scen_choices,),
                "preset_file": (
                    preset_choices,
                    {
                        "default": "(none)",
                        "tooltip": "JSON preset under lazy_subject_scene_automation/Presets/. Live UI loads/saves via extension.",
                    },
                ),
                "pass_subject_to_main_prompt": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": (
                            "ON: main prompt includes subject file description; subject_description pin is description text only (no prepend/post). "
                            "OFF: main prompt omits subject file text; subject_description pin is still the raw subject description only."
                        ),
                    },
                ),
            },
            "optional": {
                "prepend_text": (
                    "STRING",
                    {
                        "default": "",
                        "forceInput": True,
                        "tooltip": "Optional: wired prepend for prompt (replaces former on-node multiline).",
                    },
                ),
                "post_text": (
                    "STRING",
                    {
                        "default": "",
                        "forceInput": True,
                        "tooltip": "Optional: wired post text after subject block (replaces former on-node multiline).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "MODEL", "MODEL", "STRING", "CLIP", "CLIP", "STRING")
    RETURN_NAMES = (
        "prompt",
        "model_high",
        "model_low",
        "keywords",
        "clip_high",
        "clip_low",
        "subject_description",
    )
    FUNCTION = "run"
    CATEGORY = "vsaan212/automation"

    def run(
        self,
        model_high,
        model_low,
        clip_high,
        clip_low,
        subject: str,
        scenario: str,
        preset_file: str,
        pass_subject_to_main_prompt: bool = True,
        post_text: Optional[str] = None,
        prepend_text: Optional[str] = None,
    ):
        _ = preset_file  # UI / preset system; execution uses subject + scenario widgets only
        pre = (prepend_text if prepend_text is not None else "") or ""
        post = (post_text if post_text is not None else "") or ""

        rel_sub = (subject or "").strip().replace("\\", "/").strip("/")
        rel_scen = (scenario or "").strip().replace("\\", "/").strip("/")

        preview_err: List[str] = []
        subj_raw = ""
        scen_raw = ""

        if rel_sub and rel_sub != "none":
            p = os.path.join(self.subjects_root, f"{rel_sub}.txt")
            try:
                with open(p, "r", encoding="utf-8") as f:
                    subj_raw = f.read()
            except Exception as e:
                preview_err.append(f"subject file: {e}")
        if rel_scen and rel_scen != "none":
            p = os.path.join(self.scenarios_root, f"{rel_scen}.txt")
            try:
                with open(p, "r", encoding="utf-8") as f:
                    scen_raw = f.read()
            except Exception as e:
                preview_err.append(f"scenario file: {e}")

        sh, sl, sdesc, skw = parse_subject_text(subj_raw)
        ch, cl, cdesc, ckw = parse_scenario_text(scen_raw)

        hi = _merge_stacks(sh, ch)
        lo = _merge_stacks(sl, cl)

        model_h, clip_h = _apply_stack(model_high, clip_high, hi)
        model_l, clip_l = _apply_stack(model_low, clip_low, lo)

        subject_description = (sdesc or "").strip()
        subj_for_main = sdesc if pass_subject_to_main_prompt else ""
        prompt = _build_prompt(pre, post, subj_for_main, cdesc)
        keywords = _format_keywords(skw, ckw)

        if preview_err:
            err_hdr = "[Lazy automation load error]\n" + "\n".join(preview_err) + "\n"
            prompt = err_hdr + prompt
            subject_description = err_hdr + subject_description

        return (prompt, model_h, model_l, keywords, clip_h, clip_l, subject_description)


NODE_CLASS_MAPPINGS = {
    "LazySubjectSceneAutomation": LazySubjectSceneAutomation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazySubjectSceneAutomation": "Lazy-subject-and-scene-automation",
}
