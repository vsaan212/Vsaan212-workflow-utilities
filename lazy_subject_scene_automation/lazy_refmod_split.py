"""
Lazy-refmod-split — fan a SAS ``refmod`` blob into three Load H3 RefMods slots.

``mod_#`` outputs use a COMBO-labeled wildcard type so they wire into
Load H3 RefMods dropdowns (those sockets are a list of names, not the
string ``"COMBO"``). Empty slots emit ``(none)``.
"""
from __future__ import annotations

from typing import Any, Dict

from .lazy_subject_scene_automation import REFMOD_NONE, parse_refmod_blob


class _ComboAny(str):
    """Looks like COMBO in the UI; ``!=`` is always False so it matches combo lists.

    Load H3 RefMods ``mod_#`` types are ``["(none)", "my_mod", ...]``, not ``"COMBO"``.
    A plain ``"COMBO"`` return type fails prompt validation and that node's
    VALIDATE_INPUTS then reports every input as invalid. Same trick as
    CR String To Combo (AnyType).
    """

    def __ne__(self, other: object) -> bool:
        return False


# Single shared instance — must stay a str subclass, not a plain "COMBO" string.
COMBO_ANY = _ComboAny("COMBO")


def _combo_name(name: str) -> str:
    """One dropdown value: first line only, or (none)."""
    n = (name or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not n:
        return REFMOD_NONE
    line = n.splitlines()[0].strip()
    return line or REFMOD_NONE


class LazyRefmodSplit:
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "refmod": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": True,
                        "default": "",
                        "tooltip": (
                            "Single refmod blob from Lazy-subject-and-scene-automation. "
                            "Breaks out up to three subjects for Load H3 RefMods."
                        ),
                    },
                ),
            },
        }

    RETURN_TYPES = (
        COMBO_ANY,
        "FLOAT",
        "INT",
        COMBO_ANY,
        "FLOAT",
        "INT",
        COMBO_ANY,
        "FLOAT",
        "INT",
    )
    RETURN_NAMES = (
        "mod_1",
        "strength_1",
        "copies_1",
        "mod_2",
        "strength_2",
        "copies_2",
        "mod_3",
        "strength_3",
        "copies_3",
    )
    FUNCTION = "split"
    CATEGORY = "vsaan212/automation"

    def split(self, refmod: str = ""):
        slots = parse_refmod_blob(refmod)
        out = []
        for name, strength, copies in slots:
            out.append(_combo_name(name))
            out.append(float(strength))
            out.append(int(copies))
        return tuple(out)


NODE_CLASS_MAPPINGS = {
    "LazyRefmodSplit": LazyRefmodSplit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyRefmodSplit": "Lazy-refmod-split",
}
