# Lazy Model Switcher

**ComfyUI node:** `LazyModelSwitcher` · **Menu:** `vsaan212/automation`

Picks the diffusion UNET from the workflow mode string so one KSampler path can serve both FL2V and R2V MiniMax H3 models.

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `ref2video_model` | MODEL | R2V UNET (`ref2va`) |
| `text_img_fl2v_model` | MODEL | T2V / I2V / FL2V UNET (`fl2va`) |
| `selector_in` | STRING | Bare mode or tagged SAS blob. Force-input. |

## Output

| Output | Notes |
|--------|--------|
| `MODEL` | `R2V` → ref model; anything else (including empty/unknown) → text/img/FL2V model |

## Wiring

Wire both UNET loaders in, then `selector_in` from **Lazy Global Selector**, Prompt Engineer `selector_Out`, or SAS `selector`. Feed the output into **Lazy-subject-and-scene-automation** **`minimax_model`** (then that output into your guider / sampler). Global Selector does not pick the UNET — this node does.
