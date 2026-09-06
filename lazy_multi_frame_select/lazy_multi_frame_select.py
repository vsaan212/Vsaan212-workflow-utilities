"""Pause after VAE Decode, pick up to 6 frames from a grid, continue with 6 IMAGE outputs."""
from __future__ import annotations

import os
import threading
import time
import uuid
from typing import Any

import numpy as np
import torch
from PIL import Image

import folder_paths
from server import PromptServer

from ..lazy_logging import debug

MAX_SELECT = 6
DEFAULT_SHOW_EVERY = 4
THUMB_MAX_SIDE = 256
EVENT_NAME = "vsaan212-multi-frame-select"
POLL_SECONDS = 0.25

try:
    import comfy.model_management as mm
except Exception:
    mm = None

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}


def _throw_if_interrupted() -> None:
    if mm is not None and hasattr(mm, "throw_exception_if_processing_interrupted"):
        mm.throw_exception_if_processing_interrupted()


def _interrupt_prompt() -> None:
    if mm is None:
        return
    if hasattr(mm, "interrupt_current_processing"):
        mm.interrupt_current_processing()
    elif hasattr(mm, "interrupt_processing"):
        mm.interrupt_processing()


def _raise_interrupt() -> None:
    exc = getattr(mm, "InterruptProcessingException", None) if mm is not None else None
    if exc is not None:
        raise exc()
    raise RuntimeError("Lazy Multi Frame Select cancelled")


def _as_batch(images: Any) -> torch.Tensor | None:
    if images is None:
        return None
    if isinstance(images, (list, tuple)):
        parts = []
        for t in images:
            if t is None:
                continue
            parts.append(t.unsqueeze(0) if t.dim() == 3 else t)
        if not parts:
            return None
        return torch.cat(parts, dim=0)
    if not torch.is_tensor(images):
        return None
    if images.dim() == 3:
        return images.unsqueeze(0)
    return images


def _tensor_to_pil(frame: torch.Tensor) -> Image.Image:
    arr = frame.detach().cpu().float().numpy()
    if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[0] < arr.shape[-1]:
        arr = np.transpose(arr, (1, 2, 0))
    arr = np.clip(255.0 * arr, 0, 255).astype(np.uint8)
    if arr.ndim == 2:
        return Image.fromarray(arr, mode="L").convert("RGB")
    if arr.shape[-1] == 1:
        return Image.fromarray(arr[..., 0], mode="L").convert("RGB")
    if arr.shape[-1] == 4:
        return Image.fromarray(arr, mode="RGBA").convert("RGB")
    return Image.fromarray(arr[..., :3], mode="RGB")


def _grid_indices(count: int, every: int) -> list[int]:
    """0-based original frame numbers to show. Always includes the last frame."""
    every = max(1, int(every or 1))
    if count <= 0:
        return []
    idxs = list(range(0, count, every))
    last = count - 1
    if idxs[-1] != last:
        idxs.append(last)
    return idxs


def _save_thumbs(
    batch: torch.Tensor, node_id: str, indices: list[int]
) -> list[dict[str, Any]]:
    temp_dir = folder_paths.get_temp_directory()
    subfolder = "lazy_mfs"
    dest = os.path.join(temp_dir, subfolder)
    os.makedirs(dest, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(node_id))
    stamp = f"{safe_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    results: list[dict[str, Any]] = []
    n = int(batch.shape[0])
    for i in indices:
        if i < 0 or i >= n:
            continue
        pil = _tensor_to_pil(batch[i])
        pil.thumbnail((THUMB_MAX_SIDE, THUMB_MAX_SIDE), Image.Resampling.LANCZOS)
        filename = f"{stamp}_{i:04d}.jpg"
        pil.save(os.path.join(dest, filename), format="JPEG", quality=75, optimize=True)
        results.append(
            {"filename": filename, "subfolder": subfolder, "type": "temp", "index": i}
        )
    return results


def _send_to_ui(payload: dict[str, Any]) -> None:
    PromptServer.instance.send_sync(EVENT_NAME, payload)


def receive_selection(body: dict[str, Any]) -> dict[str, Any]:
    """Called from the HTTP route when the user continues or cancels."""
    node_id = str(body.get("node_id") or "")
    action = str(body.get("action") or "continue").strip().lower()
    if not node_id:
        return {"ok": False, "error": "missing node_id"}

    with _lock:
        session = _sessions.get(node_id)
        if session is None:
            return {"ok": False, "error": "not waiting"}

        if action == "cancel":
            session["cancelled"] = True
            session["indices"] = []
        else:
            raw = body.get("indices") or []
            seen: set[int] = set()
            indices: list[int] = []
            n = int(session["images"].shape[0]) if session.get("images") is not None else 0
            for item in raw:
                try:
                    idx = int(item)
                except (TypeError, ValueError):
                    continue
                if idx < 0 or idx >= n or idx in seen:
                    continue
                seen.add(idx)
                indices.append(idx)
                if len(indices) >= MAX_SELECT:
                    break
            session["indices"] = indices
            session["cancelled"] = False
        session["event"].set()

    if action == "cancel":
        _interrupt_prompt()
    return {"ok": True}


class LazyMultiFrameSelect:
    """Show every decoded frame, wait for a pick of up to 6, then emit them."""

    DESCRIPTION = (
        "Takes a VAE Decode IMAGE batch, shows every Nth frame in a grid "
        "(default 4), pauses until you pick up to 6, then continues."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": (
                    "IMAGE",
                    {
                        "tooltip": (
                            "IMAGE batch from VAE Decode (video frames). "
                            "The node pauses until you pick up to 6 frames."
                        ),
                    },
                ),
                "show_every": (
                    "INT",
                    {
                        "default": DEFAULT_SHOW_EVERY,
                        "min": 1,
                        "max": 64,
                        "step": 1,
                        "tooltip": (
                            "Show every Nth frame in the grid (1 = all frames). "
                            "Default 4. The last frame is always included."
                        ),
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE",) * MAX_SELECT
    RETURN_NAMES = tuple(f"image_{i}" for i in range(1, MAX_SELECT + 1))
    FUNCTION = "select"
    CATEGORY = "vsaan212/lazy"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def select(self, images, show_every=DEFAULT_SHOW_EVERY, unique_id=None):
        if isinstance(unique_id, (list, tuple)):
            unique_id = unique_id[0] if unique_id else None
        node_id = str(unique_id).strip() if unique_id is not None else ""
        if not node_id:
            node_id = f"tmp-{uuid.uuid4().hex[:8]}"
        batch = _as_batch(images)
        if batch is None or batch.shape[0] == 0:
            debug("Lazy Multi Frame Select", "no images; emitting empty slots")
            return (None,) * MAX_SELECT

        batch = batch.detach().contiguous().cpu()
        prompt_id = str(getattr(PromptServer.instance, "last_prompt_id", "") or "")
        every = max(1, int(show_every or 1))
        grid_idxs = _grid_indices(int(batch.shape[0]), every)
        previews = _save_thumbs(batch, node_id or "node", grid_idxs)
        event = threading.Event()
        session = {
            "event": event,
            "indices": None,
            "cancelled": False,
            "images": batch,
            "previews": previews,
        }

        with _lock:
            old = _sessions.get(node_id)
            if old is not None:
                old["cancelled"] = True
                old["event"].set()
            _sessions[node_id] = session

        debug(
            "Lazy Multi Frame Select",
            f"waiting on {len(grid_idxs)}/{batch.shape[0]} frames "
            f"(every {every}, node {node_id})",
        )
        _send_to_ui(
            {
                "node_id": node_id,
                "prompt_id": prompt_id,
                "images": previews,
                "max_select": MAX_SELECT,
                "show_every": every,
                "total_frames": int(batch.shape[0]),
            }
        )

        try:
            while not event.is_set():
                _throw_if_interrupted()
                event.wait(POLL_SECONDS)
            _throw_if_interrupted()
            if session["cancelled"]:
                debug("Lazy Multi Frame Select", "cancelled")
                _raise_interrupt()
            indices = session.get("indices") or []
        finally:
            with _lock:
                if _sessions.get(node_id) is session:
                    _sessions.pop(node_id, None)

        outs: list[Any] = [None] * MAX_SELECT
        preview_by_idx = {
            int(p["index"]): p for p in previews if p.get("index") is not None
        }
        selected_ui: list[dict[str, Any]] = []
        for slot, idx in enumerate(indices[:MAX_SELECT]):
            if 0 <= idx < batch.shape[0]:
                outs[slot] = batch[idx : idx + 1]
                if idx in preview_by_idx:
                    selected_ui.append(preview_by_idx[idx])

        debug(
            "Lazy Multi Frame Select",
            f"selected {len(indices)} frame(s): {indices}",
        )
        return {"ui": {"images": selected_ui}, "result": tuple(outs)}


NODE_CLASS_MAPPINGS = {
    "LazyMultiFrameSelect": LazyMultiFrameSelect,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyMultiFrameSelect": "Lazy Multi Frame Select",
}
