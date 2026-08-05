"""Shared MiniMax / Lazy workflow mode helpers (T2V / I2V / FL2V / R2V)."""
from __future__ import annotations

import re
from typing import Optional

MODES = ("T2V", "I2V", "FL2V", "R2V")

ROLE_FIRST_FRAME = "Image2video First frame"
ROLE_LAST_FRAME = "Image2video Last frame"
ROLE_REFERENCE = "Reference image"

WORKFLOW_ROLES = (ROLE_FIRST_FRAME, ROLE_LAST_FRAME, ROLE_REFERENCE)

_WORKFLOW_ALIASES = {
    "t2v": "T2V",
    "t2va": "T2V",
    "i2v": "I2V",
    "i2va": "I2V",
    "fl2v": "FL2V",
    "fl": "FL2V",
    "fl2va": "FL2V",
    "flf2v": "FL2V",
    "fflf": "FL2V",
    "r2v": "R2V",
    "ref2v": "R2V",
    "ref2va": "R2V",
}

_ROLE_ALIASES = {
    "image2videofirstframe": ROLE_FIRST_FRAME,
    "image2videoimagefirstframe": ROLE_FIRST_FRAME,
    "firstframe": ROLE_FIRST_FRAME,
    "i2vfirst": ROLE_FIRST_FRAME,
    "image2videolastframe": ROLE_LAST_FRAME,
    "image2videoimagelastframe": ROLE_LAST_FRAME,
    "lastframe": ROLE_LAST_FRAME,
    "referenceimage": ROLE_REFERENCE,
    "reference": ROLE_REFERENCE,
    "refimage": ROLE_REFERENCE,
    "r2v": ROLE_REFERENCE,
}


def normalize_workflow(raw: str) -> Optional[str]:
    """Normalize a mode string to T2V / I2V / FL2V / R2V, or None if unknown."""
    key = re.sub(r"[^a-z0-9]", "", (raw or "").lower())
    if not key:
        return None
    return _WORKFLOW_ALIASES.get(key)


def normalize_role(raw: str) -> Optional[str]:
    """Normalize a workflow_role widget / label to a canonical role string."""
    text = (raw or "").strip()
    if text in WORKFLOW_ROLES:
        return text
    key = re.sub(r"[^a-z0-9]", "", text.lower())
    return _ROLE_ALIASES.get(key)


def role_enabled(role: str, mode: Optional[str]) -> bool:
    """Whether an Image Loader role should emit IMAGE for the given mode.

    Empty / unknown mode → enabled (backwards compatible when selector unwired).
    """
    canonical_role = normalize_role(role) or (role or "").strip()
    if not mode:
        return True
    if mode == "T2V":
        return False
    if canonical_role == ROLE_FIRST_FRAME:
        return mode in ("I2V", "FL2V")
    if canonical_role == ROLE_LAST_FRAME:
        return mode == "FL2V"
    if canonical_role == ROLE_REFERENCE:
        return mode == "R2V"
    # Unknown role: do not block
    return True


def parse_selector_tagged(text: str) -> dict[str, str]:
    """Parse a tagged selector blob into {norm_tag: body}."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return {}
    lines = text.split("\n")
    out: dict[str, str] = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^\[([^\]]+)\]\s*$", lines[i].strip())
        if not m:
            i += 1
            continue
        tag = re.sub(r"[^a-z0-9]", "", m.group(1).lower())
        i += 1
        body_lines: list[str] = []
        while i < len(lines):
            if re.match(r"^\[([^\]]+)\]\s*$", lines[i].strip()):
                break
            body_lines.append(lines[i])
            i += 1
        body = "\n".join(body_lines).strip()
        if tag:
            out[tag] = body
    return out


def resolve_mode_from_selector(selector: str) -> Optional[str]:
    """Resolve mode from a bare mode string or a tagged `[Workflow]` blob."""
    text = (selector or "").strip()
    if not text:
        return None
    bare = normalize_workflow(text)
    if bare and "\n" not in text and not text.lstrip().startswith("["):
        return bare
    tagged = parse_selector_tagged(text)
    if "workflow" in tagged:
        return normalize_workflow(tagged["workflow"].splitlines()[0])
    # Whole blob might still be a single-line mode
    return normalize_workflow(text.splitlines()[0])
