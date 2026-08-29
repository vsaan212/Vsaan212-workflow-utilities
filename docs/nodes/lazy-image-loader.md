# Lazy Image Loader

**Menu:** `vsaan212/lazy` → **Lazy Image Loader**

Load an image from ComfyUI’s `input/` folder with optional **cover crop** to popular aspect ratios, live drag-to-reposition in the node preview, browse, drag-and-drop upload, and a button to open the input folder in your file manager.

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `IMAGE` | IMAGE | Loaded image (cropped when auto crop is on) |
| `width` | INT | Final pixel width |
| `height` | INT | Final pixel height |

## Widgets

| Widget | Default | Notes |
|--------|---------|--------|
| `image` | — | Combo of files under `input/` (including subfolders). New nodes start **empty** (no file selected, no decode) so the loader does not hold VRAM until you pick or drop an image. Upload with **Browse…** or drop onto the crop preview (not Comfy’s native Load Image thumbnail). |
| `workflow_role` | **Image2video First frame** | Role for global-selector gating: first frame / last frame / reference image |
| `aspect_ratio` | **9:16 (Phone)** | 9:16, 16:9, 1:1, 4:5, 3:4, 4:3, 2:3, 21:9, or **Original (no crop)** |
| `auto_crop` | ON | Cover-crop to the selected ratio; OFF passes the full image through |
| `resize_by_megapixels` | OFF | When ON, Lanczos-scale the result to a megapixel target (multiple of **32**), same math as Comfy **ResolutionSelector** (`MP × 1024²`) |
| `megapixels` | **0.98** | 0.2–4.0, step 0.1. Hidden in the UI while resize is OFF. Example: **0.98 @ 16:9 → 1344×768** (H3 native) |
| `offset_x` / `offset_y` | 0 | Pan position (−1…1). Updated live when you drag the preview; shown in the readout below the preview |
| `zoom` | 1.0 | Zoom in from 1× (cover crop) up to 4×. Shrinks the crop window so you can trim dead space, then pan |
| `flip_horizontal` | OFF | Mirror left ↔ right after crop (toggled from the preview toolbar) |

### Optional input

| Input | Notes |
|-------|--------|
| `global_selector_input` | STRING from [Lazy Global Selector](lazy-global-selector.md). When set, `IMAGE` is only emitted if `workflow_role` matches the mode (`T2V` → none; `I2V` → first; `FL2V` → first+last; `R2V` → reference). Otherwise returns `None` (skip load) so optional downstream sockets stay empty. Unwired selector → always emit (backwards compatible). |

## UI (browser extension)

The node includes a custom crop preview (`js/lazy_image_loader.js`). Comfy’s native Load Image thumbnail under the node is disabled so only this preview is shown:

- **Browse…** — file picker (uploads to `input/`)
- **Open input folder** — opens ComfyUI’s input directory
- **Flip horizontal** — toggle mirror; button highlights when active; preview matches output
- **Zoom** slider — 1×–4×; use with pan to cut empty sky/letterboxing
- **Pan readout** — live `Pan X · Y · Zoom` values (and **Flipped** when on; hidden Comfy sliders stay out of the way)
- **Drop** an image on the preview area to upload (isolated to this node — dropping on a stacked loader no longer updates the neighbor’s preview)
- **Drag** inside the preview to pan (more range when zoom &gt; 1×)
- Preview frame is locked to the selected aspect (no CSS stretch)

## Wiring tips

- **Lazy Global Selector:** set `workflow_role`, wire `global_selector_input`, and leave all loaders connected — unused roles emit nothing.
- **LazyPrompt — Vision Describe** or **Prompt Engineer** `first_frame` (LM Studio): wire `IMAGE` from this node after cropping to phone or target ratio.
- **MiniMax H3 / Lazy MiniMax All-in-One:** turn on **`resize_by_megapixels`**, set aspect (e.g. 16:9) and megapixels (e.g. **0.98**), then wire **`width`** / **`height`** into the MiniMax conditioner and **`IMAGE`** into `first_frame` / refs.
- **Load Image** replacement: use this node when you want framing control without a separate crop node.

### Megapixel examples (16:9, multiple=32)

| MP | Output |
|----|--------|
| 0.2 | 608×352 |
| 0.5 | 960×544 |
| 0.98 | 1344×768 |
| 1.0 | 1376×768 |
| 2.0 | 1920×1088 |

All listed aspect ratios use the same formula; **Original** uses the image’s own aspect after crop/passthrough.

## API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/lazy_image_loader/images` | GET | JSON list of image paths under `input/` |
| `/lazy_image_loader/open-input` | POST | Open input folder in the OS file manager |

## Troubleshooting

- **Node fails on load (`KeyError: 'input'`)** — fixed in v1.9.0+; uses `get_input_directory()` like ComfyUI’s built-in Load Image.
- **Preview empty after upload** — press **`R`** to refresh, or pick the file from the `image` combo.
- **Stale thumbnail under the crop preview** — that was Comfy’s native image widget; it is hidden. Restart ComfyUI (or refresh the frontend) after updating so only the adjustable crop preview remains.
- **Preview looks stretched** — display-only; output crop is unchanged. Reload the frontend if an old node size is still cached.
- **Drag-and-drop upload fails in some browsers** — use **Browse…** or copy files into `input/` and refresh.
