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
| `image` | — | Combo + ComfyUI upload; lists images under `input/` (including subfolders) |
| `aspect_ratio` | **9:16 (Phone)** | 9:16, 16:9, 1:1, 4:5, 3:4, 4:3, 2:3, 21:9, or **Original (no crop)** |
| `auto_crop` | ON | Cover-crop to the selected ratio; OFF passes the full image through |
| `offset_x` / `offset_y` | 0 | Pan position (−1…1). Updated live when you drag the preview; shown in the readout below the preview |
| `zoom` | 1.0 | Zoom in from 1× (cover crop) up to 4×. Shrinks the crop window so you can trim dead space, then pan |

## UI (browser extension)

The node includes a custom preview (`js/lazy_image_loader.js`):

- **Browse…** — file picker (uploads to `input/`)
- **Open input folder** — opens ComfyUI’s input directory
- **Center crop** — resets pan and zoom to defaults
- **Zoom** slider — 1×–4×; use with pan to cut empty sky/letterboxing
- **Pan readout** — live `Pan X · Y · Zoom` values (offsets update here when you drag; the hidden Comfy sliders stay out of the way)
- **Drop** an image on the preview area to upload
- **Drag** inside the preview to pan (more range when zoom &gt; 1×)

## Wiring tips

- **LazyPrompt — Vision Describe** or **Prompt Engineer** `image` (LM Studio): wire `IMAGE` from this node after cropping to phone or target ratio.
- **Load Image** replacement: use this node when you want framing control without a separate crop node.

## API routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/lazy_image_loader/images` | GET | JSON list of image paths under `input/` |
| `/lazy_image_loader/open-input` | POST | Open input folder in the OS file manager |

## Troubleshooting

- **Node fails on load (`KeyError: 'input'`)** — fixed in v1.9.0+; uses `get_input_directory()` like ComfyUI’s built-in Load Image.
- **Preview empty after upload** — press **`R`** to refresh, or pick the file from the `image` combo.
- **Drag-and-drop upload fails in some browsers** — use **Browse…** or copy files into `input/` and refresh.
