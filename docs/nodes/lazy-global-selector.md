# Lazy Global Selector

**ComfyUI node:** `LazyGlobalSelector` · **Menu:** `vsaan212/automation`

One dropdown for MiniMax H3 workflow mode. Fan the STRING out to Image Loaders, subject/scene automation, Prompt Engineer, MiniMax, and Model Switcher so the whole graph follows a single choice.

## Output

| Output | Type | Notes |
|--------|------|--------|
| `global_Selector_output` | STRING | Plain mode: `T2V`, `I2V`, `FL2V`, or `R2V` |

## Widget

| Widget | Default | Notes |
|--------|---------|--------|
| `workflow_type` | `I2V` | `T2V` / `I2V` / `FL2V` / `R2V` |

`FFLF` is accepted as an alias for `FL2V` on downstream nodes that normalize mode strings; this dropdown emits canonical `FL2V`.

## Wiring

1. Wire to every **Lazy Image Loader** `global_selector_input` (hard-gates IMAGE by role).
2. Wire to **Lazy-subject-and-scene-automation** `global_selector_input` (fills `[Workflow]` when files omit it). Does **not** switch SAS `model_high` / `model_low` / `minimax_model`.
3. Wire to **LazyPrompt — Prompt Engineer** `global_selector_input` (gates vision/media sockets).
4. Prefer Prompt Engineer `selector_Out` (or SAS `selector`) → MiniMax `selector` and **Lazy Model Switcher** `selector_in`. Switcher output → SAS `minimax_model`.

See [video_minimax_h3_global_selector](../workflows/video_minimax_h3_global_selector.md).
