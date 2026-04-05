"""
Lazy Subject + Scene Automation — combines subject/scenario file parsing,
optional LoRA bypass behavior, and prompt assembly for Wan 2.1 / 2.2 style stacks.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from comfy import model_management
from nodes import LoraLoader

ApplySlot = Tuple[str, float, float]  # path, strength_model, strength_clip


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


def _append_primary_subject(
    blocks: Dict[str, Tuple[str, float, float]],
    high_stack: List[ApplySlot],
    low_stack: List[ApplySlot],
) -> None:
    shb = blocks.get(_norm_tag("SubjectLoraHigh"))
    slb = blocks.get(_norm_tag("SubjectLoraLow"))
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
    _append_optional_pair(
        blocks,
        "ScenarioLoraHigh",
        "ScenarioLoraLow",
        high_stack,
        low_stack,
    )


def _subject_stacks_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> Tuple[List[ApplySlot], List[ApplySlot]]:
    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    _append_primary_subject(blocks, high, low)
    _append_optional_pair(blocks, "OptionalLoraAHigh", "OptionalLoraAlow", high, low)
    _append_optional_pair(blocks, "OptionalLoraBHigh", "OptionalLoraBlow", high, low)
    return high, low


def _scenario_stacks_from_blocks(blocks: Dict[str, Tuple[str, float, float]]) -> Tuple[List[ApplySlot], List[ApplySlot]]:
    high: List[ApplySlot] = []
    low: List[ApplySlot] = []
    _append_primary_scenario(blocks, high, low)
    _append_optional_pair(blocks, "OptionalScenarioALoraHigh", "OptionalScenarioALoraLow", high, low)
    _append_optional_pair(blocks, "OptionalScenarioBLoraHigh", "OptionalScenarioBLoraLow", high, low)
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
    """

    subjects_relpaths: List[str] = []
    scenarios_relpaths: List[str] = []
    subjects_root: str = ""
    scenarios_root: str = ""

    @classmethod
    def refresh_subjects_list(cls) -> None:
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
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        cls.refresh_subjects_list()
        cls.refresh_scenarios_list()
        subj_choices = sorted(cls.subjects_relpaths, key=lambda s: s.lower())
        scen_choices = sorted(cls.scenarios_relpaths, key=lambda s: s.lower())
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
                "prepend_text": ("STRING", {"default": "", "multiline": True}),
                "post_text": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING", "MODEL", "MODEL", "STRING", "CLIP", "CLIP")
    RETURN_NAMES = (
        "prompt",
        "model_high",
        "model_low",
        "keywords",
        "clip_high",
        "clip_low",
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
        prepend_text: str,
        post_text: str,
    ):
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

        prompt = _build_prompt(prepend_text, post_text, sdesc, cdesc)
        keywords = _format_keywords(skw, ckw)

        if preview_err:
            prompt = "[Lazy automation load error]\n" + "\n".join(preview_err) + "\n" + prompt

        return (prompt, model_h, model_l, keywords, clip_h, clip_l)


NODE_CLASS_MAPPINGS = {
    "LazySubjectSceneAutomation": LazySubjectSceneAutomation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazySubjectSceneAutomation": "Lazy-subject-and-scene-automation",
}
