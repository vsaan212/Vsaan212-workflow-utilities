"""Qwen2.5-VL image → scene_context for LazyPrompt Engineer."""
import gc
import os
import torch
import numpy as np
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")


def comfy_tensor_to_pil(tensor) -> Image.Image:
    if tensor.ndim == 4:
        tensor = tensor[0]
    arr = (tensor.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


_INSTANCE = {"processor": None, "model": None, "source": None}

DESCRIBE_PROMPT = (
    "Describe this image in one paragraph of plain sentences, around 100-130 words. "
    "Start with 'Style: photorealistic' or 'Style: anime' or 'Style: 3D animation' etc. "
    "Then describe the person naturally — their age, gender, skin tone, hair, body type, "
    "what they are wearing or doing, and any exposed body parts you can see — "
    "use plain words: breasts, nipples, pussy, penis, anus, buttocks. "
    "Describe their pose, what they are on or interacting with, "
    "the camera framing and angle, the lighting and time of day, and the setting. "
    "Write it as one flowing paragraph. Do not use bullet points, lists, or labels. "
    "If there is no person in the image, describe the scene instead — the environment, setting, lighting, time of day, mood, and any notable objects or details."
)

MODEL_OPTIONS = {
    "Qwen2.5-VL-3B — Fast (huihui abliterated)": "huihui-ai/Qwen2.5-VL-3B-Instruct-abliterated",
    "Qwen2.5-VL-7B — Better NSFW (prithiv caption)": "prithivMLmods/Qwen2.5-VL-7B-Abliterated-Caption-it",
}


class LazyPromptVisionDescribe:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "Starting frame for I2V / reference for grounding."}),
                "model_name": (
                    list(MODEL_OPTIONS.keys()),
                    {
                        "default": "Qwen2.5-VL-3B — Fast (huihui abliterated)",
                        "tooltip": "3B ~6GB VRAM; 7B slower, often better on explicit captions.",
                    },
                ),
                "offline_mode": ("BOOLEAN", {"default": False, "tooltip": "Use local cache only when ON."}),
                "local_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "placeholder": "Optional snapshot path (overrides dropdown)",
                        "tooltip": "Optional local snapshot folder; overrides HF id.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("scene_context",)
    FUNCTION = "describe"
    CATEGORY = "vsaan212/LazyPrompt"

    def describe(self, image, model_name, offline_mode, local_path):
        global _INSTANCE

        hf_id = MODEL_OPTIONS[model_name]

        if offline_mode:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
        else:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
            os.environ.pop("HF_DATASETS_OFFLINE", None)
            os.environ.pop("HF_HUB_OFFLINE", None)

        if local_path and local_path.strip():
            source = local_path.strip()
        elif offline_mode:
            source = hf_id
        else:
            try:
                from huggingface_hub import snapshot_download

                source = snapshot_download(hf_id)
            except Exception as e:
                print(f"[LazyPrompt Vision] Download failed: {e}")
                source = hf_id

        if _INSTANCE["model"] is None or _INSTANCE["source"] != source:
            if _INSTANCE["model"] is not None:
                try:
                    _INSTANCE["model"].to("cpu")
                except Exception:
                    pass
                _INSTANCE["model"] = None
                _INSTANCE["processor"] = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            print(f"[LazyPrompt Vision] Loading {model_name}...")

            _INSTANCE["processor"] = AutoProcessor.from_pretrained(
                source, local_files_only=offline_mode
            )
            _INSTANCE["model"] = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                source,
                device_map="auto",
                torch_dtype=dtype,
                local_files_only=offline_mode,
            )
            _INSTANCE["model"].eval()
            _INSTANCE["source"] = source
            print("[LazyPrompt Vision] Loaded.")

        processor = _INSTANCE["processor"]
        model = _INSTANCE["model"]

        pil_image = comfy_tensor_to_pil(image)
        print(f"[LazyPrompt Vision] Image: {pil_image.size}")

        try:
            from qwen_vl_utils import process_vision_info
        except ImportError as e:
            raise ImportError(
                "[LazyPrompt Vision] Install qwen-vl-utils: pip install qwen-vl-utils"
            ) from e

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an image description tool for an AI video pipeline. "
                    "Describe exactly what you see in plain factual prose. "
                    "Be direct and accurate. Do not embellish or invent details."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": DESCRIBE_PROMPT},
                ],
            },
        ]

        text_input = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = processor(
            text=[text_input],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(model.device)

        input_len = inputs["input_ids"].shape[1]

        tok = processor.tokenizer
        stop_ids = []
        if tok.eos_token_id is not None:
            stop_ids.append(tok.eos_token_id)
        for s in ["<|redacted_im_end|>", "<|endoftext|>"]:
            ids = tok.encode(s, add_special_tokens=False)
            if len(ids) == 1 and ids[0] not in stop_ids:
                stop_ids.append(ids[0])

        pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=180,
                temperature=0.3,
                do_sample=True,
                top_p=0.9,
                pad_token_id=pad_id,
                eos_token_id=stop_ids,
            )

        new_tokens = out[0][input_len:]
        description = tok.decode(new_tokens, skip_special_tokens=True).strip()

        del out, inputs

        print(f"[LazyPrompt Vision] Output: {len(description.split())} words.")

        print("[LazyPrompt Vision] Unloading to free VRAM...")
        try:
            _INSTANCE["model"].to("cpu")
        except Exception:
            pass
        _INSTANCE["model"] = None
        _INSTANCE["processor"] = None
        _INSTANCE["source"] = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        print("[LazyPrompt Vision] VRAM cleared.")

        return (description,)


NODE_CLASS_MAPPINGS = {
    "LazyPromptVisionDescribe": LazyPromptVisionDescribe,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyPromptVisionDescribe": "LazyPrompt — Vision Describe",
}
