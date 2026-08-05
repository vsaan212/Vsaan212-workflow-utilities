"""Lazy MiniMax H3 all-in-one conditioner.

Wraps Comfy core MiniMaxH3ImageToVideo (T2V / I2V / FL2V) and
MiniMaxH3ReferenceToVideo (R2V). Optional selector STRING from
Lazy-subject-and-scene-automation overrides wired media paths.

Uses ComfyUI V3 Autogrow inputs (same pattern as core MiniMax H3 nodes)
so reference sockets expand one-at-a-time instead of listing all slots.

Thanks to Comfy-Org / ComfyUI for native H3 nodes
(comfy_extras/nodes_minimax_h3.py, PR #15224).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import folder_paths
import nodes
import numpy as np
import torch
from PIL import Image, ImageOps
from comfy_api.latest import io

from ..workflow_modes import (
    normalize_workflow,
    parse_selector_tagged,
    resolve_mode_from_selector,
)

# Prefer core; fall back to vendored copy when Comfy < 0.30.
try:
    from comfy_extras.nodes_minimax_h3 import (
        MiniMaxH3ImageToVideo,
        MiniMaxH3ReferenceToVideo,
    )
except Exception:
    from ._nodes_minimax_h3_fallback import (  # type: ignore
        MiniMaxH3ImageToVideo,
        MiniMaxH3ReferenceToVideo,
    )


def seconds_to_h3_frames(seconds: float) -> int:
    """Workflow length snap: max(5, round(a*24)) aligned to 17k+5 grid."""
    a = float(seconds)
    base = max(5, int(round(a * 24)))
    return base + (5 - (base % 17)) % 17


def _strip_input_prefix(path: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    low = p.lower()
    if low.startswith("input/"):
        p = p[6:]
    return p.strip().lstrip("/")


def _load_image_tensor(rel_path: str) -> Optional[torch.Tensor]:
    rel = _strip_input_prefix(rel_path)
    if not rel:
        return None
    try:
        full = folder_paths.get_annotated_filepath(rel)
    except Exception:
        full = os.path.join(folder_paths.get_input_directory(), rel)
    if not full or not os.path.isfile(full):
        return None
    try:
        img = Image.open(full)
        img = ImageOps.exif_transpose(img).convert("RGB")
        arr = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(arr)[None,]
    except Exception:
        return None


def _audio_to_comfy_dict(waveform: torch.Tensor, sample_rate: int) -> Dict[str, Any]:
    """Normalize to Comfy AUDIO: {waveform: [B, C, L], sample_rate}."""
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)  # [C, L]
    if waveform.dim() == 2:
        waveform = waveform.unsqueeze(0)  # [B, C, L]
    return {"waveform": waveform.contiguous().float(), "sample_rate": int(sample_rate)}


def _load_audio_dict(rel_path: str) -> Optional[Dict[str, Any]]:
    """
    Load audio from Comfy input/ without relying on torchcodec.

    Easy-Install embeds often ship a broken torchcodec DLL (entry-point mismatch
    with torch). Prefer soundfile / stdlib wave, then torchaudio soundfile backend.
    """
    rel = _strip_input_prefix(rel_path)
    if not rel:
        return None
    try:
        full = folder_paths.get_annotated_filepath(rel)
    except Exception:
        full = os.path.join(folder_paths.get_input_directory(), rel)
    if not full or not os.path.isfile(full):
        return None

    try:
        import soundfile as sf

        data, sr = sf.read(full, dtype="float32", always_2d=True)  # [L, C]
        waveform = torch.from_numpy(data.T.copy())  # [C, L]
        return _audio_to_comfy_dict(waveform, sr)
    except Exception:
        pass

    try:
        import wave

        with wave.open(full, "rb") as wf:
            sr = wf.getframerate()
            n_ch = wf.getnchannels()
            sw = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())
        if sw == 2:
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 4:
            arr = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sw == 1:
            arr = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            raise ValueError(f"unsupported WAV sample width: {sw}")
        if n_ch > 1:
            arr = arr.reshape(-1, n_ch).T  # [C, L]
        else:
            arr = arr.reshape(1, -1)
        return _audio_to_comfy_dict(torch.from_numpy(arr.copy()), sr)
    except Exception:
        pass

    try:
        import torchaudio

        try:
            waveform, sr = torchaudio.load(full, backend="soundfile")
        except TypeError:
            try:
                torchaudio.set_audio_backend("soundfile")
            except Exception:
                pass
            waveform, sr = torchaudio.load(full)
        return _audio_to_comfy_dict(waveform, sr)
    except Exception:
        return None


def _unpack_node_output(result: Any) -> Tuple[Any, Any]:
    if result is None:
        raise RuntimeError("MiniMax H3 execute returned None")
    if hasattr(result, "args") and result.args is not None and len(result.args) >= 2:
        return result.args[0], result.args[1]
    if isinstance(result, (tuple, list)) and len(result) >= 2:
        return result[0], result[1]
    raise RuntimeError(f"Unexpected MiniMax H3 output type: {type(result)!r}")


def _as_autogrow_dict(value: Any) -> Dict[str, Any]:
    """Normalize Autogrow payload to {name: tensor} like core H3 nodes expect."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {k: v for k, v in value.items() if v is not None}
    # Some builds wrap Autogrow as an object with .values / mapping interface
    if hasattr(value, "items"):
        try:
            return {k: v for k, v in value.items() if v is not None}
        except Exception:
            pass
    return {}


class LazyMinimaxAllInOne(io.ComfyNode):
    """Auto-switching MiniMax H3 conditioner (T2V / I2V / FL2V / R2V)."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="LazyMinimaxAllInOne",
            display_name="Lazy MiniMax All-in-One",
            category="vsaan212/minimax",
            description=(
                "MiniMax H3 conditioner: auto T2V / I2V / FL2V / R2V from sockets or "
                "selector. Reference inputs use Autogrow (expand as you connect). "
                "Based on Comfy-Org MiniMax H3 core nodes."
            ),
            inputs=[
                io.Clip.Input("clip"),
                io.Vae.Input("vae"),
                io.String.Input(
                    "prompt",
                    multiline=True,
                    dynamic_prompts=True,
                    default="",
                ),
                io.Int.Input(
                    "width",
                    default=1344,
                    min=32,
                    max=nodes.MAX_RESOLUTION,
                    step=32,
                ),
                io.Int.Input(
                    "height",
                    default=768,
                    min=32,
                    max=nodes.MAX_RESOLUTION,
                    step=32,
                ),
                io.Float.Input(
                    "duration_seconds",
                    default=5.0,
                    min=0.2,
                    max=150.0,
                    step=0.1,
                    tooltip=(
                        "Clip length in seconds; snapped to H3 17k+5 frame grid at 24 fps "
                        "(5s → 124 frames)."
                    ),
                ),
                io.Combo.Input(
                    "ref_image_size",
                    options=["match", "max"],
                    default="match",
                    tooltip="R2V only. When selector is non-empty, forced to match.",
                ),
                io.Vae.Input(
                    "audio_vae",
                    optional=True,
                    tooltip=(
                        "Required for R2V (reference audio / video soundtrack encode). "
                        "Ignored for T2V / I2V / FL2V."
                    ),
                ),
                io.Image.Input("first_frame", optional=True),
                io.Image.Input("last_frame", optional=True),
                io.String.Input(
                    "selector",
                    optional=True,
                    force_input=True,
                    multiline=True,
                    default="",
                    tooltip=(
                        "Bare mode (T2V/I2V/FL2V/R2V) or tagged blob from "
                        "Lazy-subject-and-scene-automation. Non-empty path fields override "
                        "sockets; forces ref_image_size=match when tagged paths present."
                    ),
                ),
                io.Autogrow.Input(
                    "ref_images",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input(
                            "ref_image",
                            tooltip="Reference image (<Picture i>). R2V only.",
                        ),
                        prefix="ref_image_",
                        min=0,
                        max=9,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_videos",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Image.Input(
                            "ref_video",
                            tooltip="Reference video frames at 24 fps. R2V only.",
                        ),
                        prefix="ref_video_",
                        min=0,
                        max=3,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_video_audios",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Audio.Input(
                            "ref_video_audio",
                            tooltip="Soundtrack of the same-numbered reference video.",
                        ),
                        prefix="ref_video_audio_",
                        min=0,
                        max=3,
                    ),
                ),
                io.Autogrow.Input(
                    "ref_audios",
                    optional=True,
                    template=io.Autogrow.TemplatePrefix(
                        input=io.Audio.Input(
                            "ref_audio",
                            tooltip="Standalone reference audio. R2V only.",
                        ),
                        prefix="ref_audio_",
                        min=0,
                        max=3,
                    ),
                ),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Latent.Output(),
                io.String.Output(display_name="mode"),
            ],
        )

    @classmethod
    def execute(
        cls,
        clip,
        vae,
        prompt: str,
        width: int,
        height: int,
        duration_seconds: float,
        ref_image_size: str = "match",
        audio_vae=None,
        first_frame=None,
        last_frame=None,
        selector: str = "",
        ref_images=None,
        ref_videos=None,
        ref_video_audios=None,
        ref_audios=None,
    ) -> io.NodeOutput:
        length = seconds_to_h3_frames(duration_seconds)
        prompt = prompt if prompt is not None else ""

        selector_text = (selector or "").strip()
        sel = parse_selector_tagged(selector_text)
        # Tagged path overrides (not bare mode alone)
        has_path_overrides = any(
            (sel.get(f"referenceimage{i}", "") or "").strip() for i in range(1, 6)
        ) or bool((sel.get("audioreference", "") or "").strip())
        selector_active = has_path_overrides

        sel_workflow = resolve_mode_from_selector(selector_text)
        ref_paths = [
            sel.get("referenceimage1", ""),
            sel.get("referenceimage2", ""),
            sel.get("referenceimage3", ""),
            sel.get("referenceimage4", ""),
            sel.get("referenceimage5", ""),
        ]
        audio_path = sel.get("audioreference", "")

        sel_images: List[Optional[torch.Tensor]] = [
            _load_image_tensor(p) if p else None for p in ref_paths
        ]
        sel_audio = _load_audio_dict(audio_path) if audio_path else None

        eff_first = first_frame
        eff_last = last_frame

        ref_images_d = _as_autogrow_dict(ref_images)
        ref_videos_d = _as_autogrow_dict(ref_videos)
        ref_video_audios_d = _as_autogrow_dict(ref_video_audios)
        ref_audios_d = _as_autogrow_dict(ref_audios)

        for i, tensor in enumerate(sel_images):
            if tensor is not None:
                ref_images_d[f"ref_image_{i}"] = tensor

        if sel_audio is not None:
            ref_audios_d["ref_audio_0"] = sel_audio

        # Dual-use: ReferenceImage1/2 also feed first/last for I2V/FL2V
        if sel_images[0] is not None:
            eff_first = sel_images[0]
        if sel_images[1] is not None:
            eff_last = sel_images[1]

        has_refs = bool(ref_images_d) or bool(ref_videos_d) or bool(ref_audios_d)

        if sel_workflow:
            mode = sel_workflow
        elif has_refs:
            mode = "R2V"
        elif eff_first is not None and eff_last is not None:
            mode = "FL2V"
        elif eff_first is not None:
            mode = "I2V"
        else:
            mode = "T2V"

        # Hard-gate sockets by resolved mode
        if mode == "T2V":
            eff_first, eff_last = None, None
            ref_images_d, ref_videos_d, ref_video_audios_d, ref_audios_d = {}, {}, {}, {}
            has_refs = False
        elif mode == "I2V":
            eff_last = None
            ref_images_d, ref_videos_d, ref_video_audios_d, ref_audios_d = {}, {}, {}, {}
            has_refs = False
        elif mode == "FL2V":
            ref_images_d, ref_videos_d, ref_video_audios_d, ref_audios_d = {}, {}, {}, {}
            has_refs = False
        elif mode == "R2V":
            eff_first, eff_last = None, None

        if mode == "R2V":
            if audio_vae is None:
                raise ValueError(
                    "Lazy MiniMax All-in-One: audio_vae is required for R2V "
                    "(wire the MiniMax H3 audio VAE)."
                )
            size = "match" if selector_active else (ref_image_size or "match")
            result = MiniMaxH3ReferenceToVideo.execute(
                clip,
                vae,
                audio_vae,
                prompt,
                width,
                height,
                length,
                ref_image_size=size,
                ref_images=ref_images_d or None,
                ref_videos=ref_videos_d or None,
                ref_video_audios=ref_video_audios_d or None,
                ref_audios=ref_audios_d or None,
            )
        else:
            ff = eff_first if mode in ("I2V", "FL2V") else None
            lf = eff_last if mode == "FL2V" else None
            if mode == "I2V":
                lf = None
            if mode == "T2V":
                ff, lf = None, None
            result = MiniMaxH3ImageToVideo.execute(
                clip,
                vae,
                prompt,
                width,
                height,
                length,
                first_frame=ff,
                last_frame=lf,
            )

        positive, latent = _unpack_node_output(result)
        return io.NodeOutput(positive, latent, mode)


NODE_CLASS_MAPPINGS = {
    "LazyMinimaxAllInOne": LazyMinimaxAllInOne,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyMinimaxAllInOne": "Lazy MiniMax All-in-One",
}
