# Lazy-refmod-split

**ComfyUI node:** `LazyRefmodSplit` · **Menu:** `vsaan212/automation` · **Display:** Lazy-refmod-split

Fans a single **`refmod`** string from [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) into three **Load H3 RefMods** slots. Those loaders are **[Luisacaotica](https://github.com/Luisacaotica)**’s [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod) — this node only unpacks names/strengths/copies.

## Why it exists

Stacking two or three **character LoRAs** on one MiniMax graph mixes faces and outfits (LoRA bleed). RefMods put each identity on H3’s native reference path instead. SAS keeps one **`refmod`** output so the automation node does not grow eight extra sockets; this node unpacks that blob so you can wire **subject 1 / 2 / 3** into **Load H3 RefMods** `mod_#` (COMBO), `strength_#`, and `copies_#`.

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `refmod` | STRING (force input) | Blob from SAS **`refmod`**. Empty is valid (all slots `(none)`). |

## Outputs

| Output | Type | Notes |
|--------|------|--------|
| `mod_1` / `mod_2` / `mod_3` | COMBO | Single selected RefMod name (combo link), or **`(none)`** when that subject had no `[Refmod]`. Wire directly into Load H3 RefMods **`mod_#`**. |
| `strength_1` / `strength_2` / `strength_3` | FLOAT | From `[Refmod][strength]…` (default **1.0**). |
| `copies_1` / `copies_2` / `copies_3` | INT | From the optional third bracket (default **1**, range 1–10). |

## Wiring

1. Subject files use **`[Refmod][strength][copies]`** with the Load H3 RefMods name as the body (see SAS node doc).
2. Set SAS **`multisubject_refmod`** to **1**, **2**, or **3** (0 still emits the blob if tags exist, but does **not** skip LoRAs).
3. SAS **`refmod`** → this node **`refmod`**.
4. On **Load H3 RefMods**, convert **only** the `mod_#` / `strength_#` / `copies_#` rows you will use **to inputs**. Leave unused rows as widgets on `(none)`. **`mod_#`** is a COMBO-colored link that matches the loader dropdown (same compatibility as CR String To Combo). Unused split slots stay `(none)` / `1.0` / `1`.
5. Load H3 RefMods **`mods`** → **Apply H3 RefMod** as usual.

Empty SAS blob → all three names are `(none)` so the loader skips those rows.

## Linked `mod_#` and `'None' not found in mods/`

Load H3 RefMods runs **VALIDATE_INPUTS at queue time**, before SAS or this split node execute. A converted `mod_#` input is then Python `None`, which that pack stringifies to `'None'` and rejects.

You do **not** need to fork [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod). This pack wraps that validator so unresolved / empty names are treated as `(none)` until the graph actually runs (when the real dropdown name is applied). Restart ComfyUI after updating.

If MiniMaxH3Mod is not installed, the wrap is a no-op.

## Blob format

SAS writes tagged rows (omitting empty subjects):

```text
[Refmod1][1.0][1]
vanellope_example
[Refmod2][0.85][2]
other_character
```

## See also

- [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) — `[Refmod]` tag, multi-subject slots, LoRA skip rules.
