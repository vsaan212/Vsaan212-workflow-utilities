"""Lazy Switch nodes — pick on_true / on_false by matching an upstream text value."""
from __future__ import annotations

import re


def _matches(compare: str, match: str, case_sensitive: bool) -> bool:
    """True when compare equals match, or equals any alternative in a list.

    ``match`` may be a single value or several alternatives separated by
    commas or pipes (e.g. ``t2v,r2v`` or ``T2V | R2V``).
    """
    left = (compare or "").strip()
    right = (match or "").strip()
    if not case_sensitive:
        left = left.lower()
        right = right.lower()
    if not right:
        return left == ""
    alts = [p.strip() for p in re.split(r"[,|]", right) if p.strip()]
    if len(alts) <= 1:
        return left == (alts[0] if alts else "")
    return left in alts


class _LazySwitchBase:
    """Shared match + lazy branch selection for typed switch nodes."""

    CATEGORY = "vsaan212/utilities"
    FUNCTION = "switch"

    @classmethod
    def check_lazy_status(cls, compare, match, on_true=None, on_false=None, case_sensitive=False):
        if _matches(compare, match, case_sensitive):
            return ["on_true"]
        return ["on_false"]

    def switch(self, compare, match, on_true, on_false, case_sensitive=False):
        if _matches(compare, match, case_sensitive):
            return (on_true,)
        return (on_false,)


class LazySwitchFloat(_LazySwitchBase):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "compare": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": False,
                        "default": "",
                        "tooltip": "Upstream text to test (e.g. selector / mode string).",
                    },
                ),
                "match": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "When compare equals this, output on_true; otherwise on_false. "
                            "Use commas or pipes for alternatives (e.g. t2v,r2v)."
                        ),
                    },
                ),
                "on_true": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": -1e9,
                        "max": 1e9,
                        "step": 0.01,
                        "lazy": True,
                        "tooltip": "Value when compare matches match.",
                    },
                ),
                "on_false": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -1e9,
                        "max": 1e9,
                        "step": 0.01,
                        "lazy": True,
                        "tooltip": "Value when compare does not match.",
                    },
                ),
                "case_sensitive": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "When off, compare and match are trimmed and compared case-insensitively.",
                    },
                ),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("FLOAT",)


class LazySwitchInt(_LazySwitchBase):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "compare": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": False,
                        "default": "",
                        "tooltip": "Upstream text to test (e.g. selector / mode string).",
                    },
                ),
                "match": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "When compare equals this, output on_true; otherwise on_false. "
                            "Use commas or pipes for alternatives (e.g. t2v,r2v)."
                        ),
                    },
                ),
                "on_true": (
                    "INT",
                    {
                        "default": 1,
                        "min": -2_147_483_647,
                        "max": 2_147_483_647,
                        "step": 1,
                        "lazy": True,
                        "tooltip": "Value when compare matches match.",
                    },
                ),
                "on_false": (
                    "INT",
                    {
                        "default": 0,
                        "min": -2_147_483_647,
                        "max": 2_147_483_647,
                        "step": 1,
                        "lazy": True,
                        "tooltip": "Value when compare does not match.",
                    },
                ),
                "case_sensitive": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "When off, compare and match are trimmed and compared case-insensitively.",
                    },
                ),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("INT",)


class LazySwitchText(_LazySwitchBase):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "compare": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": False,
                        "default": "",
                        "tooltip": "Upstream text to test (e.g. selector / mode string).",
                    },
                ),
                "match": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "When compare equals this, output on_true; otherwise on_false. "
                            "Use commas or pipes for alternatives (e.g. t2v,r2v)."
                        ),
                    },
                ),
                "on_true": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "lazy": True,
                        "tooltip": "Value when compare matches match.",
                    },
                ),
                "on_false": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "lazy": True,
                        "tooltip": "Value when compare does not match.",
                    },
                ),
                "case_sensitive": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "When off, compare and match are trimmed and compared case-insensitively.",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)


NODE_CLASS_MAPPINGS = {
    "LazySwitchFloat": LazySwitchFloat,
    "LazySwitchInt": LazySwitchInt,
    "LazySwitchText": LazySwitchText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazySwitchFloat": "Lazy Switch (Float)",
    "LazySwitchInt": "Lazy Switch (Integer)",
    "LazySwitchText": "Lazy Switch (Text)",
}
