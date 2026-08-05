from __future__ import annotations

import math
import os
import platform
import subprocess

import numpy as np
import torch
from PIL import Image, ImageOps

import folder_paths

from ..workflow_modes import (
    ROLE_FIRST_FRAME,
    WORKFLOW_ROLES,
    normalize_workflow,
    role_enabled,
)

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

# Integer aspect pairs for megapixel sizing (Comfy ResolutionSelector style)
ASPECT_RATIO_WH: dict[str, tuple[int, int] | None] = {
    "9:16 (Phone)": (9, 16),
    "16:9 (Landscape)": (16, 9),
    "1:1 (Square)": (1, 1),
    "4:5 (Instagram)": (4, 5),
    "3:4 (Portrait)": (3, 4),
    "4:3 (Classic)": (4, 3),
    "2:3 (Photo)": (2, 3),
    "21:9 (Ultrawide)": (21, 9),
    "Original (no crop)": None,
}

DEFAULT_ASPECT = "9:16 (Phone)"
DEFAULT_MEGAPIXELS = 0.98
MP_MULTIPLE = 32


def size_from_megapixels(
    megapixels: float,
    w_ratio: float,
    h_ratio: float,
    multiple: int = MP_MULTIPLE,
) -> tuple[int, int]:
    """Comfy ResolutionSelector math: MP uses 1024², round to `multiple`."""
    wr = float(w_ratio)
    hr = float(h_ratio)
    if wr <= 0 or hr <= 0:
        wr, hr = 1.0, 1.0
    total_pixels = float(megapixels) * 1024 * 1024
    scale = math.sqrt(total_pixels / (wr * hr))
    width = int(round(wr * scale / multiple) * multiple)
    height = int(round(hr * scale / multiple) * multiple)
    return max(multiple, width), max(multiple, height)


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
    zoom: float = 1.0,
) -> tuple[int, int, int, int]:
    """Cover-crop box: (left, top, width, height).

    offset_* in [-1, 1], 0 = centered pan within available range.
    zoom >= 1 shrinks the crop window (zoom in) from the cover-crop baseline.
    """
    zoom = max(1.0, float(zoom))
    src_ratio = src_w / float(src_h)

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = max(1, int(round(src_h * target_ratio)))
    else:
        crop_w = src_w
        crop_h = max(1, int(round(src_w / target_ratio)))

    crop_w = max(1, int(round(crop_w / zoom)))
    crop_h = max(1, int(round(crop_h / zoom)))

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
                "workflow_role": (
                    list(WORKFLOW_ROLES),
                    {
                        "default": ROLE_FIRST_FRAME,
                        "tooltip": (
                            "Which MiniMax / Prompt Engineer role this loader feeds. "
                            "Paired with global_selector_input to hard-gate the IMAGE output."
                        ),
                    },
                ),
                "aspect_ratio": (list(ASPECT_RATIOS.keys()), {"default": DEFAULT_ASPECT}),
                "auto_crop": ("BOOLEAN", {"default": True}),
                "resize_by_megapixels": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": (
                            "When ON, scale the (cropped) image to width×height from "
                            "megapixels × aspect (Comfy ResolutionSelector math, multiple of 32). "
                            "Wire those outputs into MiniMax width/height."
                        ),
                    },
                ),
                "megapixels": (
                    "FLOAT",
                    {
                        "default": DEFAULT_MEGAPIXELS,
                        "min": 0.2,
                        "max": 4.0,
                        "step": 0.1,
                        "tooltip": (
                            "Target megapixels (0.2–4.0). Uses 1024² units like ResolutionSelector. "
                            "0.98 @ 16:9 → 1344×768 (H3 native)."
                        ),
                    },
                ),
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
                "zoom": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 1.0,
                        "max": 4.0,
                        "step": 0.05,
                        "display": "slider",
                    },
                ),
                "flip_horizontal": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "global_selector_input": (
                    "STRING",
                    {
                        "forceInput": True,
                        "default": "",
                        "multiline": False,
                        "tooltip": (
                            "From Lazy Global Selector. When set, IMAGE is only emitted if "
                            "workflow_role matches the mode (else None — optional downstream)."
                        ),
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("IMAGE", "width", "height")
    FUNCTION = "load_image"
    CATEGORY = "vsaan212/lazy"

    @classmethod
    def IS_CHANGED(
        cls,
        image,
        workflow_role=ROLE_FIRST_FRAME,
        aspect_ratio=DEFAULT_ASPECT,
        auto_crop=True,
        resize_by_megapixels=False,
        megapixels=DEFAULT_MEGAPIXELS,
        offset_x=0.0,
        offset_y=0.0,
        zoom=1.0,
        flip_horizontal=False,
        global_selector_input="",
    ):
        return (
            f"{image}|{workflow_role}|{aspect_ratio}|{auto_crop}|{bool(resize_by_megapixels)}"
            f"|{float(megapixels):.2f}|{offset_x:.4f}|{offset_y:.4f}"
            f"|{zoom:.4f}|{bool(flip_horizontal)}|{global_selector_input or ''}"
        )

    @classmethod
    def VALIDATE_INPUTS(cls, image, **kwargs):
        if not image:
            return "Select or upload an image."
        if not folder_paths.exists_annotated_filepath(image):
            return f"Image not found: {image}"
        return True

    def load_image(
        self,
        image: str,
        workflow_role: str = ROLE_FIRST_FRAME,
        aspect_ratio: str = DEFAULT_ASPECT,
        auto_crop: bool = True,
        resize_by_megapixels: bool = False,
        megapixels: float = DEFAULT_MEGAPIXELS,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        zoom: float = 1.0,
        flip_horizontal: bool = False,
        global_selector_input: str = "",
    ):
        mode = normalize_workflow(global_selector_input or "")
        if not role_enabled(workflow_role, mode):
            return (None, 0, 0)

        pil = load_pil_image(image)
        target_ratio = ASPECT_RATIOS.get(aspect_ratio)

        if auto_crop and target_ratio is not None:
            left, top, crop_w, crop_h = compute_crop_box(
                pil.width,
                pil.height,
                target_ratio,
                offset_x,
                offset_y,
                zoom,
            )
            pil = pil.crop((left, top, left + crop_w, top + crop_h))

        if flip_horizontal:
            pil = ImageOps.mirror(pil)

        if resize_by_megapixels:
            wh = ASPECT_RATIO_WH.get(aspect_ratio)
            if wh is None:
                g = math.gcd(pil.width, pil.height) or 1
                wr, hr = pil.width / g, pil.height / g
            else:
                wr, hr = float(wh[0]), float(wh[1])
            tw, th = size_from_megapixels(float(megapixels), wr, hr, MP_MULTIPLE)
            if (pil.width, pil.height) != (tw, th):
                pil = pil.resize((tw, th), Image.Resampling.LANCZOS)

        tensor = pil_to_tensor(pil)
        return (tensor, pil.width, pil.height)


NODE_CLASS_MAPPINGS = {
    "LazyImageLoader": LazyImageLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyImageLoader": "Lazy Image Loader",
}
