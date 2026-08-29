# Lazy MiniMax All-in-One

**ComfyUI node:** `LazyMinimaxAllInOne` · **Menu:** `vsaan212/minimax`

Auto-switching MiniMax H3 conditioner that covers **T2V**, **I2V**, **FL2V** (first+last), and **R2V** in one node. Delegates to Comfy core `MiniMaxH3ImageToVideo` / `MiniMaxH3ReferenceToVideo`.

**Thanks to [Comfy-Org / ComfyUI](https://github.com/Comfy-Org/ComfyUI)** for native H3 support (`comfy_extras/nodes_minimax_h3.py`, [PR #15224](https://github.com/Comfy-Org/ComfyUI/pull/15224)).

Requires **ComfyUI 0.30.0+** with MiniMax H3 installed. You still load the correct diffusion UNET upstream (`fl2va` for T2V/I2V/FL2V, `ref2va` for R2V); this node outputs a **`mode`** string so you can switch models yourself.

## Mode selection

1. If optional **`selector`** is a bare mode string (`T2V` / `I2V` / `FL2V` / `R2V`, aliases like `FFLF`→`FL2V`) or a tagged blob with `[Workflow]`, that wins.
2. Else infer from wired / selector media: any reference image/video/audio → **R2V**; first+last → **FL2V**; first only → **I2V**; else → **T2V**.
3. Empty prompt + no media → **T2V** with blank prompt (no error).

Sockets are hard-gated by the resolved mode (unused frames/refs are ignored even if wired). When the selector blob contains path overrides, **`ref_image_size`** is forced to **`match`**.

## Inputs

| Input | Notes |
|-------|--------|
| `clip` / `vae` | Required (Qwen3-VL text encoder + video VAE). |
| `prompt` | May be empty. |
| `width` / `height` | Canvas (multiples of 32). |
| `duration_seconds` | Converted to H3 frame length: `max(5, round(s*24))` snapped to the 17k+5 grid (5s → 124). |
| `ref_image_size` | R2V only (`match` / `max`). Forced to `match` when selector is connected and non-empty. |
| `audio_vae` | **R2V only** — required when mode is R2V. Ignored for T2V/I2V/FL2V. |
| `first_frame` / `last_frame` | I2V / FL2V. |
| `ref_images` | Autogrow **0–9** reference images (R2V). Extra sockets appear as you connect. Prompt tags: `<Picture 1>`… |
| `ref_videos` / `ref_video_audios` | Autogrow **0–3** reference videos + soundtracks. |
| `ref_audios` | Autogrow **0–3** standalone reference audio. |
| `selector` | Optional STRING: bare mode or tagged blob from subject/scene automation / Prompt Engineer. |

## Outputs

| Output | Notes |
|--------|--------|
| `positive` | CONDITIONING for the sampler. |
| `latent` | Empty MiniMax H3 AV latent. |
| `mode` | `T2V` / `I2V` / `FL2V` / `R2V` — use to pick the matching UNET. |

## Wiring with subject/scene automation

1. Put `[Workflow]`, `[ReferenceImage1]`…`[ReferenceImage5]`, `[AudioReference]` in subject and/or scenario `.txt` files (before `[desciption]` / `[Prompt]`).
2. Paths are relative to ComfyUI `input/` (e.g. `chars/hero.png` or `input/chars/hero.png`). Backslashes are fine on Windows.
3. Wire automation **`selector`** → this node’s **`selector`**, or a bare mode from [Lazy Global Selector](lazy-global-selector.md). Disk `[ReferenceImageN]` / `[AudioReference]` overlay matching Autogrow slots only (`ref_image_1`, `ref_audio_1`); other wired refs stay.
4. For UNET routing, wire mode → [Lazy Model Switcher](lazy-model-switcher.md).

Audio files (`.wav` / etc.) are loaded via **soundfile** or stdlib **wave**, not torchcodec — Easy-Install embeds often hit a broken `libtorchcodec_core*.dll` entry-point error if torchaudio defaults to torchcodec.
