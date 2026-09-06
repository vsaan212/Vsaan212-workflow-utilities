import json
import os
import threading


class StorageManager:
    _lock = threading.Lock()

    @staticmethod
    def _get_filepath():
        from ..lazy_user_data import lazy_prompts_path

        return lazy_prompts_path()

    @classmethod
    def load_prompts(cls):
        with cls._lock:
            filepath = cls._get_filepath()
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                return {}
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

    @classmethod
    def save_prompt(cls, name, text):
        with cls._lock:
            filepath = cls._get_filepath()
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    prompts = json.load(f)
            else:
                prompts = {}
            prompts[name] = text
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)

    @classmethod
    def delete_prompt(cls, name):
        with cls._lock:
            filepath = cls._get_filepath()
            if not os.path.exists(filepath):
                return
            with open(filepath, "r", encoding="utf-8") as f:
                prompts = json.load(f)
            prompts.pop(name, None)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_prompt_names(cls):
        prompts = cls.load_prompts()
        return sorted(prompts.keys())


class LazyPromptSaver:
    @classmethod
    def INPUT_TYPES(cls):
        names = StorageManager.get_prompt_names()
        return {
            "required": {
                "prompt_name": ("STRING", {"default": ""}),
                "prompt_text": ("STRING", {"multiline": True, "default": ""}),
                "saved_prompts": (["-- None --"] + names,),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt_text",)
    FUNCTION = "execute"
    CATEGORY = "vsaan212/utilities"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def execute(self, prompt_name, prompt_text, saved_prompts):
        from ..lazy_logging import debug
        debug("Lazy Prompt Saver", f"passing through '{prompt_name or saved_prompts}'")
        return (prompt_text,)
