# custom_nodes/optional_switch_lora/__init__.py
# OptionalSwitchLoRA: if command == "bypass" (case-insensitive) -> no-op, else call stock LoraLoader

import os
from comfy import model_management
from nodes import LoraLoader

class OptionalSwitchLoRA:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                # command: if equals "bypass" -> do nothing. Otherwise treated as name/path.
                "command_or_path": ("STRING", {"multiline": False}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP",)
    FUNCTION = "apply"
    CATEGORY = "vsaan212/LoRA"

    def apply(self, model, clip, command_or_path, strength_model, strength_clip):
        # normalize
        cmd = (command_or_path or "").strip().strip('"').strip("'")
        if cmd.lower() == "bypass" or cmd == "":
            # explicit bypass or empty -> return unchanged
            return (model, clip)

        # treat cmd as a path or a basename; if it's a path, register its dir
        path = cmd
        if os.path.exists(path):
            lora_dir = os.path.dirname(os.path.abspath(path))
            lora_name = os.path.basename(path)
            model_management.lora_paths.add(lora_dir)
        else:
            # treat as a name that should already be discoverable by LoraLoader
            lora_name = cmd

        # delegate to stock LoraLoader (keeps existing behavior)
        loader = LoraLoader()
        out_model, out_clip = loader.load_lora(model, clip, lora_name, strength_model, strength_clip)
        return (out_model, out_clip)

NODE_CLASS_MAPPINGS = {
    "OptionalSwitchLoRA": OptionalSwitchLoRA,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Vsaan_OptionalSwitchLoRA": "Optional Switch LoRA (bypasses on 'bypass' or empty string)",
}
