"""
Compatibility for ComfyUI-MiniMaxH3Mod Load H3 RefMods.

That node’s VALIDATE_INPUTS runs at prompt-validate time, before SAS / Lazy-refmod-split
have executed. Linked ``mod_#`` values are then Python ``None``, which becomes the
string ``"None"`` and fails: ``'None' not found in mods/``.

We wrap VALIDATE_INPUTS so unresolved / empty names are treated as ``(none)``.
The real name is still applied when the graph runs. We do not copy their loader.
"""
from __future__ import annotations

import sys
import logging
from typing import Any, Optional

from .lazy_logging import debug

_log = logging.getLogger("vsaan212")

_PATCHED_ATTR = "_vsaan212_unresolved_mod_ok"
_TARGET_CLASSES = ("MiniMaxH3RefModsLoader", "MiniMaxH3RefModsAxis")


def _is_placeholder_mod_name(raw: Any, none_token: str = "(none)") -> bool:
    if raw is None:
        return True
    s = str(raw).strip()
    if not s:
        return True
    if s == none_token:
        return True
    # Python None stringified during pre-run VALIDATE_INPUTS
    if s == "None":
        return True
    return False


def _find_node_class(class_name: str) -> Optional[type]:
    try:
        import nodes as comfy_nodes

        cls = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get(class_name)
        if isinstance(cls, type):
            return cls
    except Exception:
        pass
    for mod in list(sys.modules.values()):
        try:
            cls = getattr(mod, class_name, None)
        except Exception:
            continue
        if isinstance(cls, type) and callable(getattr(cls, "VALIDATE_INPUTS", None)):
            return cls
    return None


def _wrap_validate(cls: type) -> None:
    if getattr(cls, _PATCHED_ATTR, False):
        return
    original = getattr(cls, "VALIDATE_INPUTS", None)
    if original is None:
        return
    orig_fn = getattr(original, "__func__", original)

    @classmethod
    def VALIDATE_INPUTS(inner_cls, **kwargs: Any):
        none = getattr(inner_cls, "NONE", "(none)")
        cleaned = dict(kwargs)
        for key, raw in list(cleaned.items()):
            if not str(key).startswith("mod"):
                continue
            if _is_placeholder_mod_name(raw, none):
                cleaned[key] = none
        return orig_fn(inner_cls, **cleaned)

    cls.VALIDATE_INPUTS = VALIDATE_INPUTS
    setattr(cls, _PATCHED_ATTR, True)
    debug("lazy_h3_refmod_compat", f"patched {cls.__name__}.VALIDATE_INPUTS for unresolved links")
    _log.info(
        "Patched %s.VALIDATE_INPUTS so linked RefMod slots can be empty until SAS runs",
        cls.__name__,
    )


def patch_minimax_h3_refmods_validate() -> int:
    """Wrap MiniMax H3 RefMod loader validation if that pack is installed. Returns count newly patched."""
    n = 0
    for name in _TARGET_CLASSES:
        cls = _find_node_class(name)
        if cls is None or getattr(cls, _PATCHED_ATTR, False):
            continue
        _wrap_validate(cls)
        if getattr(cls, _PATCHED_ATTR, False):
            n += 1
    return n
