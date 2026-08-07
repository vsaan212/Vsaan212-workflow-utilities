# Lazy Switch (Float / Integer / Text)

**ComfyUI nodes:** `LazySwitchFloat`, `LazySwitchInt`, `LazySwitchText` · **Menu:** `vsaan212/utilities`

| Display name | Class | `on_true` / `on_false` / output |
|--------------|-------|----------------------------------|
| Lazy Switch (Float) | `LazySwitchFloat` | `FLOAT` |
| Lazy Switch (Integer) | `LazySwitchInt` | `INT` |
| Lazy Switch (Text) | `LazySwitchText` | `STRING` |

## What it does

Compares an upstream **text** value against a **match** string. If they match, the node outputs **`on_true`**; otherwise **`on_false`**.

Only the selected branch is evaluated (`lazy` inputs + `check_lazy_status`), so expensive upstream work on the unused side is skipped.

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| **`compare`** | `STRING` (force input) | Current text from upstream (selector, mode string, etc.). |
| **`match`** | `STRING` | Literal to match against `compare`. Comma- or pipe-separated alternatives are OR’d (e.g. `t2v,r2v` or `T2V \| R2V`). |
| **`on_true`** | typed | Used when `compare` matches `match`. Lazy. |
| **`on_false`** | typed | Used when it does not match. Lazy. |
| **`case_sensitive`** | `BOOLEAN` | Default **off**: trim + case-insensitive compare. |

## Workflow usage

1. Wire a mode / selector / label string into **`compare`**.
2. Set **`match`** to the value that should pick the true branch (e.g. `R2V`, `bypass`, `T2V`). Use `t2v,r2v` when both modes should share the same branch.
3. Set or wire **`on_true`** / **`on_false`** (constants on the node, or connected outputs).
4. Use the typed output downstream (steps, strength, prompt text, etc.).

Example: Global Selector mode → Lazy Switch (Float) with `match=R2V`, `on_true=0.85`, `on_false=0.65` for mode-dependent CFG.

MiniMax Auto width/height: `match=t2v,r2v`, **`on_true`** = ResolutionSelector size, **`on_false`** = first-frame width/height (I2V / FL2V).

## See also

- [Lazy Model Switcher](lazy-model-switcher.md) — mode string → UNET branch
- [Lazy Global Selector](lazy-global-selector.md) — emits the mode string these switches often compare
