# Lazy-subject-and-scene-automation

**ComfyUI node:** `LazySubjectSceneAutomation` · **Menu:** `vsaan212/automation`

Combines optional-switch LoRA behavior, subject/scenario file selection, and formatted prompt output for **dual high/low** Wan-style workflows (and similar two-branch model graphs).

## File locations (important)

This node reads **only** from:

- `lazy_subject_scene_automation/SubjectFiles/`
- `lazy_subject_scene_automation/ScenarioFiles/`

It does **not** use the folders for [Subject Selector](subject-selector.md) or [Scenario Selector](scenario-selector.md). Copy or symlink `.txt` files if you want the same definitions in both places.

## Workflow overview

1. Load your checkpoint (or upstream stack) into **two** model branches if your workflow expects separate high/low noise models.
2. Connect **`model_high`** / **`clip_high`** and **`model_low`** / **`clip_low`** from those branches.
3. Pick **`subject`** and **`scenario`** from the dropdowns (`.txt` paths without extension).
4. Optional: fill **`prepend_text`** and **`post_text`** for framing around the subject description.
5. Use **`prompt`** for CLIP / preview / downstream text; use **`model_high`**, **`model_low`**, **`clip_high`**, **`clip_low`** as the conditioned outputs for the rest of the graph.
6. Use **`keywords`** for trigger tags or secondary conditioning if your workflow needs them.

Dropdown lists refresh when the node is created; use ComfyUI **`R`** after adding new `.txt` files. Endpoints: `/vsaan212/lazy-subject-scene/subjects` and `…/scenarios`.

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `model_high` | MODEL | High-noise branch; receives subject LoRAs then scenario LoRAs for the **high** stack. |
| `model_low` | MODEL | Low-noise branch; same for the **low** stack. |
| `clip_high` | CLIP | Patched alongside `model_high`. |
| `clip_low` | CLIP | Patched alongside `model_low`. |
| `subject` | dropdown | `.txt` under `lazy_subject_scene_automation/SubjectFiles/` (recursive). |
| `scenario` | dropdown | `.txt` under `lazy_subject_scene_automation/ScenarioFiles/` (recursive). |
| `prepend_text` | STRING | Prepended to the built prompt (see [Prompt output layout](#prompt-output-layout)). |
| `post_text` | STRING | Inserted after the subject description, before the scenario description. |

## Outputs

| Output | Notes |
|--------|--------|
| `prompt` | Readable layout for preview nodes (newlines / blank lines; see below). |
| `model_high` / `model_low` | After merged LoRA stacks. |
| `keywords` | `KeywordA/B/C` from the subject file, then from the scenario file, joined with `", "` and a trailing `", "` when non-empty. |
| `clip_high` / `clip_low` | After the same stacks as the paired model outputs. |

## LoRA application order

On each branch, LoRAs are applied in order:

1. **Subject:** primary → optional A → optional B  
2. **Scenario:** primary → optional A → optional B  

Paths can be absolute or names discoverable by ComfyUI’s `LoraLoader`. Missing optional sections in the file behave like **bypass**.

## Wan 2.1 vs 2.2 (no separate low file)

If a **low** slot is missing or set to `bypass` while the matching **high** slot has a real path, the node uses **Wan 2.1 style**: the same LoRA is applied on **both** branches; on the **low** branch **clip strength is forced to 1.0** (the high branch uses strengths from the file). This applies to subject primary, subject optionals, and scenario blocks that share the same high/low pairing rules.

---

## Subject file formats

Files are **v1** (legacy `#` sections) unless the first substantive line starts with `[` (**v2** tagged format).

### v1 — legacy

Sections separated by a line that contains only `#` (with newlines in the usual pattern):

1. First path — applied on **both** high and low model stacks (strength 1.0, clip 1.0).
2. Second path — same (optional body / extra LoRA).
3. Final section — plain **subject description** text (no LoRA).

Example:

```text
wan lora\girls\test.safetensors
#
wan lora\bodys\testbodytype.safetensors
#
Text description of the subject
```

If there is only **one** path section before the description, that single LoRA is duplicated to both stacks.

### v2 — tagged

- Tag line: `[TagName][model_strength][clip_strength]` — bracketed values are optional; missing numbers default to **1.0**.
- Following lines (until the next tag line) are the **body**: LoRA path, the word `bypass` (case-insensitive), or keyword/description text.
- Optional lines are not requiered. if not present it will treat it as if it was set to bypass.

**Subject tags (LoRA order)**

| Tag | Role |
|-----|------|
| `SubjectLoraHigh` / `SubjectLoraLow` | Primary subject LoRAs. |
| `OptionalLoraAHigh` / `OptionalLoraAlow` | Optional pair A (`OptionalLoraALow` accepted). |
| `OptionalLoraBHigh` / `OptionalLoraBlow` | Optional pair B (`OptionalLoraBLow` accepted). |
| `KeywordA` / `KeywordB` / `KeywordC` | Merged into `keywords` output. |
| `description` or `desciption` | Subject description in the final `prompt`. |

Example (mixed optional + bypass):

```text
[SubjectLoraHigh][1.0]
wan lora\girls\testH.safetensors
[SubjectLoraLow][1.0]
wan lora\girls\testL.safetensors
[OptionalLoraAHigh][1.0]
wan lora\bodytype\slimH.safetensors
[OptionalLoraAlow][1.0]
wan lora\bodytype\slimL.safetensors
[OptionalLoraBHigh][1.0]
bypass
[OptionalLoraBlow][1.0]
bypass
[KeywordA]
T3st
[KeywordB]
Sl1m
[desciption]
a test subject
```

---

## Scenario file formats

### v1 — legacy

Same `#` separators as subject v1, but paths map to stacks separately: **first** path → **high** stack only, **second** → **low** stack only, **last** section → scenario description.

If only **one** path section exists before the description, that LoRA is applied to **both** stacks.
- Optional lines are not requiered. if not present it will treat it as if it was set to bypass.

### v2 — tagged

| Tag | Role |
|-----|------|
| `ScenarioLoraHigh` / `ScenarioLoraLow` | Main scenario LoRAs. |
| `OptionalScenarioALoraHigh` / `OptionalScenarioALoraLow` | Optional pair A. |
| `OptionalScenarioBLoraHigh` / `OptionalScenarioBLoraLow` | Optional pair B. |
| `KeywordA` / `KeywordB` / `KeywordC` | Appended after subject keywords in `keywords`. |
| `description` or `desciption` | Scenario text; appears after the subject block in `prompt`. |

Example:

```text
[ScenarioLoraHigh][1.0][0.7]
wan lora\wan2.2 loras\both i2v and t2v\Aesthetics\23High noise-Aesthetics.safetensors
[ScenarioLoraLow][1.0][0.7]
wan lora\wan2.2 loras\both i2v and t2v\Aesthetics\56Low noise-Aesthetics.safetensors
[OptionalScenarioALoraHigh][1.0]
wan lora\...\56Low noise-Jump.safetensors
[OptionalScenarioALoraLow][1.0]
wan lora\...\56Low noise-Jump.safetensors
[OptionalScenarioBLoraHigh][1.0]
bypass
[OptionalScenarioBLoraLow][1.0]
bypass
[KeywordA]
Aesthetics
[desciption]
A blond girl jumps on a trampoline
```

---

## Prompt output layout

The node builds:

1. `prepend_text` plus a **newline** when prepend is non-empty.  
2. Subject `description`.  
3. A **blank line**, then `post_text` (when post is non-empty and something precedes it).  
4. A **blank line**, then scenario `description` (when both sides have text).

Use **`none.txt`** (or equivalent bypass-only files) in the dropdowns when you want no LoRAs or empty descriptions from that side.

## See also

- [Optional Switch LoRA](optional-switch-lora.md) — same bypass/path semantics for a single LoRA step.
- [Subject Selector](subject-selector.md) / [Scenario Selector](scenario-selector.md) — load raw text only from different folders.
