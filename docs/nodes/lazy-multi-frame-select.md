# Lazy Multi Frame Select

**ComfyUI node:** `LazyMultiFrameSelect` · **Menu:** `vsaan212/lazy` · **Display:** Lazy Multi Frame Select · **Pack:** v1.14.0

Takes an **IMAGE** batch (typically **VAE Decode** of a video latent), shows **every frame** in a grid on the node, **pauses the workflow**, and waits until you pick up to **6** frames and click **Continue**. Those stills come out on six IMAGE outputs in **click order**.

After a ComfyUI / pack update, **restart ComfyUI** so `js/lazy_multi_frame_select.js` loads. A frontend refresh (`R`) is not always enough the first time.

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `images` | IMAGE | Batch from VAE Decode (or any IMAGE batch). Shape `(N, H, W, C)`. A single image is treated as a batch of 1. |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `image_1` … `image_6` | IMAGE | Selected frames in **click order**. Unused slots are `None` (safe for optional IMAGE sockets). |

There are no extra widgets. Selection happens on the node UI while the prompt is running.

## Operator flow

1. Wire **VAE Decode** `IMAGE` → this node’s `images`. Wire the six outputs to whatever should receive stills (or leave unused sockets empty).
2. **Queue Prompt**. Upstream work (sample, decode) runs as usual. When this node is reached it stays **executing** and the grid fills with thumbnails.
3. Click frames to select them. A **gold border** and a slot badge **1–6** show pick order. Click a selected frame again to drop it; later badges renumber.
4. **Continue** — this node finishes and everything downstream runs with the chosen stills.
5. **Clear** empties the current pick (still waiting). **Cancel** interrupts the whole prompt (same idea as ComfyUI’s stop).

**Do not queue a second prompt** to “confirm” the pick. Continue on this node is what unblocks the run that is already in progress. A second queue starts a new wait.

Continue with nothing selected emits six empty slots.

### Selection order

| Click | Output |
|-------|--------|
| 1st frame you click | `image_1` |
| 2nd | `image_2` |
| … | … |
| 6th | `image_6` |

Small numbers on the thumbnails are **1-based batch indices** (frame 1 is the first decoded image), not output slots. Output slots are the gold badges.

Maximum **6** picks. Further clicks do nothing until you deselect one.

## Wiring examples

### MiniMax H3 / [Lazy MiniMax All-in-One](lazy-minimax-all-in-one.md)

Typical use: decode a generated clip, pick key stills, feed them back as first/last/refs.

| Output | MiniMax socket | Modes |
|--------|----------------|-------|
| `image_1` | `first_frame` | I2V, FL2V |
| `image_2` | `last_frame` | FL2V |
| `image_3` … `image_6` | `ref_image_*` (autogrow) | R2V |

You can also send any slot into Prompt Engineer / Vision Describe as `first_frame`, `image`, or `reference_image_*`.

### Other

- **Save Image / Preview** on a single slot to dump one still.
- Leave unused outputs **unwired**. Empty/`None` does not inject a dummy image.

The node is an **output node**, so it still runs if nothing is connected to the six IMAGE sockets (preview / pick only).

## UI (browser extension)

`js/lazy_multi_frame_select.js` draws the grid (Comfy’s native image strip on the node is hidden):

- Scrollable thumbnail grid (auto-fill columns)
- Status: idle / waiting / selected / cancelled
- **Continue**, **Clear**, **Cancel**
- Dragging on a thumbnail selects it instead of moving the node

Resize the node to see more frames at once. Long clips (e.g. ~100 decoded frames) scroll inside the grid.

## Behaviour notes

- The node **always pauses** on every queue (`IS_CHANGED` is never cached). Last run’s grid stays visible until the next wait.
- Frames are copied to **CPU** before the pause so this node does not keep the GPU batch. Upstream VAE output is still held by the graph until this node finishes.
- Thumbnails are JPEG previews in Comfy’s **temp** folder (`lazy_mfs/`). Full-resolution tensors are what the six outputs emit.

## API

| Route | Method | Purpose |
|-------|--------|---------|
| `/vsaan212/multi-frame-select` | POST | `{ action: "continue" \| "cancel", node_id, prompt_id, indices }` |

Python pushes thumbnails over websocket event `vsaan212-multi-frame-select`, then blocks until this POST (or ComfyUI interrupt).

## Troubleshooting

- **Grid stays empty while the node is running** — restart ComfyUI so the pack JS loads; then queue again. Press **`R`** after a restart if the canvas looks stale.
- **Clicks drag the node instead of selecting** — you are on an older JS file; restart ComfyUI.
- **Prompt never continues** — click **Continue** on this node. Do not queue again.
- **Cancel vs Clear** — Clear only drops the current selection. Cancel stops the whole prompt.
- **Downstream got fewer images than expected** — unused slots are empty. Wire only the outputs you picked, or pick more frames before Continue.
- **Two of these nodes in one graph** — each pauses on its own grid; Continue the one that is currently executing.

## See also

- [Lazy Image Loader](lazy-image-loader.md) — load / crop a still from `input/`
- [Lazy MiniMax All-in-One](lazy-minimax-all-in-one.md) — consume first/last/ref stills
- [LazyPrompt](lazyprompt.md) — Vision Describe / Prompt Engineer image sockets
