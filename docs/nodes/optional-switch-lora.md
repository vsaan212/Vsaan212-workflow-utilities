# Optional Switch LoRA

**ComfyUI node:** `OptionalSwitchLoRA` · **Menu:** `vsaan212/LoRA` · **Display:** Optional Switch LoRA (bypasses on 'bypass' or empty string)

## What it does

Applies one LoRA to a **MODEL** + **CLIP** pair using ComfyUI’s stock `LoraLoader` logic — **unless** the path/command is `bypass` or empty, in which case inputs pass through unchanged.

## Workflow usage

1. Chain **`model`** and **`clip`** from your checkpoint loader (or previous LoRA).
2. Set **`command_or_path`** to either:
   - `bypass` (case-insensitive) or leave empty → no LoRA applied.
   - A LoRA **file path** (if the file exists, its directory is registered on the fly), **or** a name your Comfy install can already resolve.
3. Tune **`strength_model`** and **`strength_clip`** (defaults 1.0).

## Why use it

- Toggle variants without rewiring: drive `command_or_path` from a primitive, switch, or upstream string node.
- Stack several Optional Switch LoRAs in series for optional style / character layers.
- Pairs well with file-based workflows that emit either a path or the word `bypass`.

## Dual-CLIP (e.g. Wan 2.2)

This node patches **one** CLIP at a time. For high/low CLIP splits, use **two** instances (same path and strengths if you want matching behavior) or use [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md), which applies stacks to `clip_high` and `clip_low` separately.

## See also

[Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) — batch subject + scenario LoRA stacks with bypass semantics.
