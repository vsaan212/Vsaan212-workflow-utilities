"""Lazy Model Switcher — pick FL2V vs R2V UNET from workflow mode."""
from __future__ import annotations

from ..workflow_modes import resolve_mode_from_selector


class LazyModelSwitcher:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ref2video_model": ("MODEL",),
                "text_img_fl2v_model": ("MODEL",),
                "selector_in": (
                    "STRING",
                    {
                        "forceInput": True,
                        "multiline": False,
                        "default": "",
                        "tooltip": (
                            "Workflow mode from Lazy Global Selector or Prompt Engineer "
                            "selector_Out (bare or tagged). R2V → ref2video_model; "
                            "else → text/img/FL2V model."
                        ),
                    },
                ),
            }
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("MODEL",)
    FUNCTION = "switch"
    CATEGORY = "vsaan212/automation"

    def switch(self, ref2video_model, text_img_fl2v_model, selector_in: str = ""):
        mode = resolve_mode_from_selector(selector_in)
        if mode == "R2V":
            return (ref2video_model,)
        return (text_img_fl2v_model,)


NODE_CLASS_MAPPINGS = {
    "LazyModelSwitcher": LazyModelSwitcher,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyModelSwitcher": "Lazy Model Switcher",
}
