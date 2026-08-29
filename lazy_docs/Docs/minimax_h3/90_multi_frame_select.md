---
title: Pick frames after decode
index: 90
---

# Pick frames after VAE Decode

**Lazy Multi Frame Select** sits after **VAE Decode**. It shows every decoded frame in a grid on the node, **pauses** the prompt, and waits until you pick up to **six** stills and click **Continue**.

Menu: `vsaan212/lazy` → **Lazy Multi Frame Select**. Full reference: the pack file `docs/nodes/lazy-multi-frame-select.md`.

## Why use it

You generated a clip and want a few **keyframes** — start pose, end pose, identity refs — without saving the video, hunting through files, and loading them again.

## Quick steps

1. Wire **VAE Decode** `IMAGE` into this node.
2. Queue. Wait until the grid fills (the node stays executing).
3. Click up to six frames. Gold badges **1–6** are output order (first click → `image_1`).
4. Click **Continue** (not Queue again).
5. Wire `image_1`…`image_6` into MiniMax first/last/refs, Vision Describe, or Save Image.

**Clear** drops the pick but keeps waiting. **Cancel** stops the prompt.

## MiniMax wiring

- `image_1` → first frame (I2V / FL2V)
- `image_2` → last frame (FL2V)
- remaining slots → R2V reference images

Unused outputs can stay unwired.

## If the grid is empty

Restart ComfyUI after installing or updating this pack so the node’s JavaScript loads, then queue once more.
