"""Lazy Global Selector — one dropdown for T2V / I2V / FL2V / R2V."""
from __future__ import annotations

from ..workflow_modes import MODES


class LazyGlobalSelector:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_type": (
                    list(MODES),
                    {
                        "default": "I2V",
                        "tooltip": (
                            "Workflow mode fan-out: wire to Image Loaders, SAS, "
                            "Prompt Engineer, MiniMax, and Model Switcher."
                        ),
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("global_Selector_output",)
    FUNCTION = "select"
    CATEGORY = "vsaan212/automation"

    def select(self, workflow_type: str):
        return (workflow_type,)


NODE_CLASS_MAPPINGS = {
    "LazyGlobalSelector": LazyGlobalSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyGlobalSelector": "Lazy Global Selector",
}
