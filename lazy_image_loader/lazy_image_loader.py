from __future__ import annotations

import os
import platform
import subprocess

import numpy as np
import torch
from PIL import Image, ImageOps

import folder_paths

# width:height label → numeric width/height ratio
ASPECT_RATIOS: dict[str, float | None] = {
    "9:16 (Phone)": 9 / 16,
    "16:9 (Landscape)": 16 / 9,
    "1:1 (Square)": 1.0,
    "4:5 (Instagram)": 4 / 5,
    "3:4 (Portrait)": 3 / 4,
    "4:3 (Classic)": 4 / 3,
    "2:3 (Photo)": 2 / 3,
    "21:9 (Ultrawide)": 21 / 9,
    "Original (no crop)": None,
}

DEFAULT_ASPECT = "9:16 (Phone)"

def list_input_images() -> list[str]:
    """List images under ComfyUI input/. Works on current ComfyUI (no folder_names 'input')."""
    input_dir = folder_paths.get_input_directory()
    if not os.path.isdir(input_dir):
        return []

    # Older ComfyUI builds registered "input" in folder_names_and_paths.
    try:
        if "input" in folder_paths.folder_names_and_paths:
            return sorted(folder_paths.get_filename_list("input"), key=lambda s: s.lower())
    except (KeyError, Exception):
        pass

    try:
        files, _ = folder_paths.recursive_search(input_dir, excluded_dir_names=[".git"])
        images = folder_paths.filter_files_content_types(files, ["image"])
    except Exception:
        files = [
            f
            for f in os.listdir(input_dir)
            if os.path.isfile(os.path.join(input_dir, f))
        ]
        images = folder_paths.filter_files_content_types(files, ["image"])

    return sorted([f.replace("\\", "/") for f in images], key=lambda s: s.lower())


def open_input_folder() -> str:
    path = folder_paths.get_input_directory()
    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
    return path


def compute_crop_box(
    src_w: int,
    src_h: int,
    target_ratio: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> tuple[int, int, int, int]:
    """Cover-crop box: (left, top, width, height). offset_* in [-1, 1], 0 = centered."""
    src_ratio = src_w / float(src_h)

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = max(1, int(round(src_h * target_ratio)))
    else:
        crop_w = src_w
        crop_h = max(1, int(round(src_w / target_ratio)))

    max_ox = max(0, src_w - crop_w) / 2.0
    max_oy = max(0, src_h - crop_h) / 2.0

    ox = float(np.clip(offset_x, -1.0, 1.0))
    oy = float(np.clip(offset_y, -1.0, 1.0))

    left = int(round((src_w - crop_w) / 2.0 + ox * max_ox))
    top = int(round((src_h - crop_h) / 2.0 + oy * max_oy))

    left = max(0, min(src_w - crop_w, left))
    top = max(0, min(src_h - crop_h, top))
    return left, top, crop_w, crop_h


def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    arr = np.array(image.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


def load_pil_image(filename: str) -> Image.Image:
    path = folder_paths.get_annotated_filepath(filename)
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


class LazyImageLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": (
                    list_input_images(),
                    {"image_upload": True},
                ),
                "aspect_ratio": (list(ASPECT_RATIOS.keys()), {"default": DEFAULT_ASPECT}),
                "auto_crop": ("BOOLEAN", {"default": True}),
                "offset_x": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.01,
                        "display": "slider",
                    },
                ),
                "offset_y": (
                    "FLOAT",
                    {
                        "default": 0.0,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.01,
                        "display": "slider",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("IMAGE", "width", "height")
    FUNCTION = "load_image"
    CATEGORY = "vsaan212/lazy"

    @classmethod
    def IS_CHANGED(cls, image, aspect_ratio, auto_crop, offset_x, offset_y):
        return f"{image}|{aspect_ratio}|{auto_crop}|{offset_x:.4f}|{offset_y:.4f}"

    @classmethod
    def VALIDATE_INPUTS(cls, image):
        if not image:
            return "Select or upload an image."
        if not folder_paths.exists_annotated_filepath(image):
            return f"Image not found: {image}"
        return True

    def load_image(
        self,
        image: str,
        aspect_ratio: str,
        auto_crop: bool,
        offset_x: float,
        offset_y: float,
    ):
        pil = load_pil_image(image)
        target_ratio = ASPECT_RATIOS.get(aspect_ratio)

        if auto_crop and target_ratio is not None:
            left, top, crop_w, crop_h = compute_crop_box(
                pil.width,
                pil.height,
                target_ratio,
                offset_x,
                offset_y,
            )
            pil = pil.crop((left, top, left + crop_w, top + crop_h))

        tensor = pil_to_tensor(pil)
        return (tensor, pil.width, pil.height)


NODE_CLASS_MAPPINGS = {
    "LazyImageLoader": LazyImageLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyImageLoader": "Lazy Image Loader",
}
