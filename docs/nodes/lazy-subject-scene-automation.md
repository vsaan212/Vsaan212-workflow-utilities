# Lazy-subject-and-scene-automation

**ComfyUI node:** `LazySubjectSceneAutomation` · **Menu:** `vsaan212/automation`

For an end-to-end workflow narrative (how the node, Python module, HTTP routes, and `lazy_subject_scene_live.js` fit together), see **[lazy-subject-scene-automation-workflow.md](../workflows/lazy-subject-scene-automation-workflow.md)**.

Combines optional-switch LoRA behavior, subject/scenario file selection, and formatted prompt output for **dual high/low** Wan-style workflows (and similar two-branch model graphs).

## File locations (important)

This node reads **only** from:

- `lazy_subject_scene_automation/SubjectFiles/`
- `lazy_subject_scene_automation/ScenarioFiles/`

It does **not** use the folders for [Subject Selector](subject-selector.md) or [Scenario Selector](scenario-selector.md). Copy or symlink `.txt` files if you want the same definitions in both places.

### Default files (seeding)

When the node refreshes its subject/scenario lists (on node creation, **`R`**, or the lazy `/vsaan212/lazy-subject-scene/…` endpoints), it ensures **`SubjectFiles/`** and **`ScenarioFiles/`** exist. If either folder is missing **`none.txt`** or **`Bypass and format example.txt`**, those files are **created** using the current **v2** minimal bypass template (`[LoraHighA]` / `[LoraLowA]` / `[desciption]`). Existing files are **not** overwritten—pull the repo or edit by hand to adopt a new template.

## Workflow overview

1. Load your checkpoint (or upstream stack) into **two** model branches if your workflow expects separate high/low noise models.
2. Connect **`model_high`** / **`clip_high`** and **`model_low`** / **`clip_low`** from those branches.
3. Pick **`subject`** and **`scenario`** from the dropdowns (`.txt` paths without extension).
4. Optional: connect **`prepend_text`** / **`post_text`** (STRING sockets only) for framing around the subject description—no on-node multiline boxes; the extension shows **live** subject/scenario file text instead.
5. Use **`prompt`** for CLIP / preview / downstream text; use **`model_high`**, **`model_low`**, **`clip_high`**, **`clip_low`** as the conditioned outputs for the rest of the graph.
6. Use **`keywords`** for trigger tags or secondary conditioning if your workflow needs them.

Dropdown lists refresh when the node is created; use ComfyUI **`R`** after adding new `.txt` files. Endpoints: `/vsaan212/lazy-subject-scene/subjects`, `…/scenarios`, and `…/presets` (see below).

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `model_high` | MODEL | High-noise branch; receives subject LoRAs then scenario LoRAs for the **high** stack. |
| `model_low` | MODEL | Low-noise branch; same for the **low** stack. |
| `clip_high` | CLIP | Patched alongside `model_high`. |
| `clip_low` | CLIP | Patched alongside `model_low`. |
| `subject` | dropdown | `.txt` under `lazy_subject_scene_automation/SubjectFiles/` (recursive). |
| `scenario` | dropdown | `.txt` under `lazy_subject_scene_automation/ScenarioFiles/` (recursive). |
| `preset_file` | dropdown | JSON presets under `lazy_subject_scene_automation/Presets/` (no `.json` in the list). `js/lazy_subject_scene_live.js` loads a preset into the dropdowns + live panes; **`Save preset`** writes one JSON snapshot. |
| `pass_subject_to_main_prompt` | BOOLEAN | As before. |
| `prepend_text` | STRING (optional, **socket only**) | Wired text prepended to the built prompt; empty if unconnected. |
| `post_text` | STRING (optional, **socket only**) | Wired text after the subject block; empty if unconnected. |

## Outputs

| Output | Notes |
|--------|--------|
| `prompt` | Readable layout for preview nodes (newlines / blank lines; see below). |
| `model_high` / `model_low` | After merged LoRA stacks. |
| `keywords` | `KeywordA/B/C` from the subject file, then from the scenario file, joined with `", "` and a trailing `", "` when non-empty. |
| `clip_high` / `clip_low` | After the same stacks as the paired model outputs. |

## LoRA application order

On each branch, LoRAs are applied in order:

1. **Subject:** slot A → slot B → slot C (`LoraHighA` / `LoraLowA` through `LoraHighC` / `LoraLowC` in the subject file).
2. **Scenario:** slot A → slot B → slot C (same tag names in the scenario file).

Paths can be absolute or names discoverable by ComfyUI’s `LoraLoader`. Missing optional sections in the file behave like **bypass**.

## Wan 2.1 vs 2.2 (no separate low file)

If a **low** slot is missing or set to `bypass` while the matching **high** slot has a real path, the node uses **Wan 2.1 style**: the same LoRA is applied on **both** branches; on the **low** branch **clip strength is forced to 1.0** (the high branch uses strengths from the file). This applies to subject and scenario blocks that share the same high/low pairing rules.

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

**Subject tags (LoRA order)** — same slot names as in scenario files; meaning comes from which folder the file lives in.

| Tag | Role |
|-----|------|
| `LoraHighA` / `LoraLowA` | Primary subject LoRAs (slot A). |
| `LoraHighB` / `LoraLowB` | Optional pair (slot B). |
| `LoraHighC` / `LoraLowC` | Optional pair (slot C). |
| `KeywordA` / `KeywordB` / `KeywordC` | Merged into `keywords` output. |
| `description` or `desciption` | Subject description in the final `prompt`. |

**Deprecated (still read):** `SubjectLoraHigh` / `SubjectLoraLow` for slot A; `OptionalLoraAHigh` / `OptionalLoraAlow` for slot B; `OptionalLoraBHigh` / `OptionalLoraBlow` for slot C. Prefer the `LoraHigh*` / `LoraLow*` names in new files.

Example (mixed optional + bypass):

```text
[LoraHighA][1.0]
wan lora\girls\testH.safetensors
[LoraLowA][1.0]
wan lora\girls\testL.safetensors
[LoraHighB][1.0]
wan lora\bodytype\slimH.safetensors
[LoraLowB][1.0]
wan lora\bodytype\slimL.safetensors
[LoraHighC][1.0]
bypass
[LoraLowC][1.0]
bypass
[KeywordA]
T3st
[KeywordB]
Sl1m
[desciption]
a test subject
```

Minimal bypass-only example (no LoRAs; description only):

```text
[LoraHighA]
Bypass
[LoraLowA]
bypass
[desciption]
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
| `LoraHighA` / `LoraLowA` | Main scenario LoRAs (slot A). |
| `LoraHighB` / `LoraLowB` | Optional pair (slot B). |
| `LoraHighC` / `LoraLowC` | Optional pair (slot C). |
| `KeywordA` / `KeywordB` / `KeywordC` | Appended after subject keywords in `keywords`. |
| `description` or `desciption` | Scenario text; appears after the subject block in `prompt`. |

**Deprecated (still read):** `ScenarioLoraHigh` / `ScenarioLoraLow` for slot A; `OptionalScenarioALoraHigh` / `OptionalScenarioALoraLow` for slot B; `OptionalScenarioBLoraHigh` / `OptionalScenarioBLoraLow` for slot C.

Example:

```text
[LoraHighA][1.0][0.7]
wan lora\wan2.2 loras\both i2v and t2v\Aesthetics\23High noise-Aesthetics.safetensors
[LoraLowA][1.0][0.7]
wan lora\wan2.2 loras\both i2v and t2v\Aesthetics\56Low noise-Aesthetics.safetensors
[LoraHighB][1.0]
wan lora\...\56Low noise-Jump.safetensors
[LoraLowB][1.0]
wan lora\...\56Low noise-Jump.safetensors
[LoraHighC][1.0]
bypass
[LoraLowC][1.0]
bypass
[KeywordA]
Aesthetics
[desciption]
A blond girl jumps on a trampoline
```

---

## Live preview, presets, and HTTP API

The extension **`js/lazy_subject_scene_live.js`** (loaded via the pack `WEB_DIRECTORY`):

- Shows **read-only** live text for the selected **subject** and **scenario** `.txt` files (refreshed when those combos change, without running the graph).
- Shows an editable **`scenario_template`** area used only for **preset JSON** (default structure uses v2 tags `LoraHighA` … `LoraLowC`, `KeywordA`–`KeywordC`, `desciption`). Execution still reads **disk** scenario files from the **`scenario`** dropdown; the template is stored in presets for your next workflow step.
- **`Save preset`** prompts for a name and `POST`s to **`/vsaan212/lazy-subject-scene/save_preset`**, then refreshes the live panes. After a successful save, the server emits WebSocket event **`vsaan212.lazy_subject_scene.presets`** so all lazy nodes update their **`preset_file`** lists without reloading the page.

| Method | Path | Body / notes |
|--------|------|----------------|
| `GET` | `/vsaan212/lazy-subject-scene/presets` | Returns `{"presets": ["rel/path", ...]}` (no `(none)`). |
| `GET` | `/vsaan212/lazy-subject-scene/default_scenario_template` | Returns `{"scenario_template": "..."}` for seeding the preset editor. |
| `POST` | `/vsaan212/lazy-subject-scene/read_pair` | JSON `{"subject":"rel","scenario":"rel"}` → `subject_text`, `scenario_text`, optional `subject_error` / `scenario_error`. |
| `POST` | `/vsaan212/lazy-subject-scene/load_preset` | JSON `{"preset":"rel/no_ext"}` → preset fields + embedded file texts. |
| `POST` | `/vsaan212/lazy-subject-scene/save_preset` | JSON `name`, `subject`, `scenario`, `prepend_text`, `post_text`, `pass_subject_to_main_prompt`, `scenario_template` → writes `Presets/{name}.json`. |

Legacy alias: `load_preset` also accepts `"filename"` instead of `"preset"`.

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
