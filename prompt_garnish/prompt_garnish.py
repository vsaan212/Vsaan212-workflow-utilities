"""
Prompt Garnish — append any number of phrases from a customizable list to base text with a joiner (e.g. ", ").
"""

from __future__ import annotations


def _parse_selected_indices(s: str) -> list[int]:
    out: list[int] = []
    if not s:
        return out
    for part in str(s).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            continue
    # unique, sorted ascending (stable order)
    return sorted(set(out))


class Vsaan_PromptGarnish:
    """
    Pick any number of lines from `phrase_list` (one phrase per line) and append them to
    `source` using `joiner` between every segment (source → phrase₁ → phrase₂ → …).

    `source` is optional: a STRING input only (no on-node text box). If disconnected, it is
    treated as empty so the node can start a workflow from phrases alone or accept upstream text.

    `selected_indices` is a comma-separated list of 0-based line indices, e.g. ``0,2`` for the
    first and third lines.

    Example: lines "Subtle high resolution" and "subtle denoise" selected with source "a photo"
    and joiner ", " → ``a photo, Subtle high resolution, subtle denoise``
    """

    @classmethod
    def INPUT_TYPES(cls):
        default_lines = "\n".join(
            [
                "Subtle high resolution",
                "subtle color correction",
                "subtle denoise",
            ]
        )
        return {
            "required": {
                "phrase_list": ("STRING", {"multiline": True, "default": default_lines}),
                "joiner": ("STRING", {"default": ", "}),
                "selected_indices": ("STRING", {"default": ""}),
            },
            "optional": {
                "source": ("STRING", {"default": "", "forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output", "selected_phrase")
    FUNCTION = "garnish"
    CATEGORY = "vsaan212/Text"
    OUTPUT_NODE = False

    def garnish(self, phrase_list: str, joiner: str, selected_indices: str, source: str | None = None):
        src = (source if source is not None else "") or ""
        lines = [ln.strip() for ln in (phrase_list or "").splitlines() if ln.strip()]
        j = joiner if joiner is not None else ", "

        if not lines:
            out = src.rstrip()
            return (out, "")

        raw_idx = _parse_selected_indices(selected_indices or "")
        valid = [i for i in raw_idx if 0 <= i < len(lines)]
        chosen = [lines[i] for i in valid]

        base = src.rstrip()

        if not chosen:
            return (base, "")

        tail = j.join(chosen)
        if not base:
            return (tail, tail)

        combined = base + j + tail
        return (combined, tail)


NODE_CLASS_MAPPINGS = {
    "Vsaan_PromptGarnish": Vsaan_PromptGarnish,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Vsaan_PromptGarnish": "Prompt Garnish",
}
