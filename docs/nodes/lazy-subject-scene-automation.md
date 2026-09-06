# Lazy-subject-and-scene-automation

**ComfyUI node:** `LazySubjectSceneAutomation` · **Menu:** `vsaan212/automation`

For an end-to-end workflow narrative (how the node, Python module, HTTP routes, and `lazy_subject_scene_live.js` fit together), see **[lazy-subject-scene-automation-workflow.md](../workflows/lazy-subject-scene-automation-workflow.md)**.

Combines optional-switch LoRA behavior, subject/scenario file selection, and formatted prompt output for **Wan dual high/low** stacks **or** singular-model graphs.

- **Wan:** wire **`model_high`** / **`clip_high`** (and **`model_low`** / **`clip_low`**). File tags **`LoraHighA–C`** / **`LoraLowA–C`** (legacy aliases still work).
- **MiniMax H3:** wire Lazy Model Switcher into **`minimax_model`**. File tags **`VideoModelLoraA–D`**. CLIP can stay on **`clip_high`** as the LoRA companion.
- **Krea2 / Z-Image / Flux:** wire **`image_model`**. File tags **`ImageModelLoraA–D`**.
- **LTX 2.x:** wire **`video_model`**. Same **`VideoModelLoraA–D`** tags as MiniMax.

**`global_selector_input`** only fills **`[Workflow]`** when files omit it. It does **not** switch High / Low / Minimax sockets.

**`video_length`** (seconds) replaces **`[video_length]`** in **`prompt`** / **`prompt_override`**, or appends a **`[video_length]`** block. **`[Time]`** is left alone (time of day). Prompt Engineer keeps that block in the LLM user message and uses it for clip duration / beat pacing.

**Recent (v1.17.0):** Multi-character MiniMax H3 **RefMods** ([Luisacaotica](https://github.com/Luisacaotica)/[ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod)): `[Refmod]` in the subject file, **`multisubject_refmod`**, and [Lazy-refmod-split](lazy-refmod-split.md) → Load H3 RefMods. Mode **1+** skips that subject’s LoRAs so identity does not **bleed** across characters. Linked `mod_#` is treated as `(none)` at queue time (no fork of his loader). User libraries live in **`ComfyUI/lazynodes/`**.

**Recent (v1.16.0):** User libraries live in **`ComfyUI/lazynodes/`** (subjects, scenarios, `lazy_prompts.json`) so Manager updates of this pack no longer wipe them. Missing folders/files are created from shipped defaults on startup; existing files are never overwritten.

**Recent (v1.15.0):** **`multisubject_refmod`** 0–3 plus optional **`subject_2`** / **`subject_3`**. Subject files may include **`[Refmod][strength][copies]`** for [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod). Mode **1+** skips that subject’s LoRAs when `[Refmod]` is present. **`refmod`** output → [Lazy-refmod-split](lazy-refmod-split.md) → Load H3 RefMods.

**Recent (v1.9.3):** **`model_low`** / **`clip_low`** optional (single-model workflows); **`{a|b|c}`** random picks use `secrets` and **`IS_CHANGED`** cache busting so choices vary every queue; live pane sync on queue via **`beforeQueuePrompt`**; non-empty live buffers preferred over disk on run.

**Recent (v1.8.0):** scenario **`[Prompt]`** → **`prompt_override`** output (LazyPrompt **`prompt_override_input`**), **`{a|b|c}`** random choices in scenario text, multiline **`[Prompt]`** bodies (bracket lines no longer truncate), README workflow screenshot + wiring guide.

## File locations (important)

This node reads **only** from:

- `ComfyUI/lazynodes/lazy_subject_scene_automation/SubjectFiles/`
- `ComfyUI/lazynodes/lazy_subject_scene_automation/ScenarioFiles/`

Those folders sit **next to** `custom_nodes/` (ComfyUI’s install root), so Manager / zip updates of this pack do **not** delete your libraries. On first startup the pack **creates** `lazynodes/` if it is missing and **copies shipped defaults** (and any leftover files still in the old pack folders) **without overwriting** files that already exist.

It does **not** use the folders for [Subject Selector](subject-selector.md) or [Scenario Selector](scenario-selector.md). Copy or symlink `.txt` files if you want the same definitions in both places.

### Default files (seeding)

When the node refreshes its subject/scenario lists (on node creation, **`R`**, or the lazy `/vsaan212/lazy-subject-scene/…` endpoints), it ensures the **lazynodes** SubjectFiles/ScenarioFiles folders exist. If either folder is missing **`none.txt`** or **`Bypass and format example.txt`**, those files are **created** using the current **v2** minimal bypass template (`[LoraHighA]` / `[LoraLowA]` / `[desciption]`). Existing files are **not** overwritten—pull the repo or edit by hand to adopt a new template.

## Workflow overview

1. **Wan:** load high-noise into **`model_high`** / **`clip_high`**. For dual stacks also wire **`model_low`** / **`clip_low`**. **MiniMax:** TxtImg UNET + reference UNET → Lazy Model Switcher → **`minimax_model`** (leave High/Low unwired). **Image:** wire **`image_model`**. **LTX:** wire **`video_model`**.
2. Pick **`subject`**, **`scenario`**, and optionally **`scenario_2`** from the dropdowns (`.txt` paths without extension). Set **`scenario_2`** to `none` when you only need one scenario file. For MiniMax multi-character RefMods, set **`multisubject_refmod`** to **1**, **2**, or **3** and (when 2–3) pick **`subject_2`** / **`subject_3`**.
4. Optional: connect **`prepend_text`** / **`post_text`** (STRING sockets only) for framing around the subject description.
5. Edit **subject / scenario / scenario 2** in the live panes on the node (subject 2 / 3 panes appear when those slots are active). **Queue uses the pane text**, not necessarily what is on disk. Use **Save edits** to write non-empty panes back to the selected `.txt` files.
6. When **`scenario_2`** is not `none`, use **`scenario_2_high_strength`** and **`scenario_2_low_strength`** to override model strength on the `[LoraHighA]` / `[LoraLowA]` lines in the scenario 2 live text (sliders initialize from the file on load).
7. Use **`prompt`** for CLIP / preview / downstream text; use **`model_high`** / **`clip_high`** (and optional **`model_low`** / **`clip_low`**) as the conditioned outputs for the rest of the graph.
8. Use **`keywords`** for trigger tags or secondary conditioning if your workflow needs them.
9. Wire **`subject_description`** → LazyPrompt **`character`** and **`prompt_override`** → **`prompt_override_input`** when using scenario **`[Prompt]`** blocks with the LLM path.

Dropdown lists refresh when the node is created; use ComfyUI **`R`** after adding new `.txt` files. Endpoints: `/vsaan212/lazy-subject-scene/subjects` and `…/scenarios` (see below).

## Inputs

| Input | Type | Notes |
|-------|------|--------|
| `model_high` | MODEL | **Optional.** Wan high-noise branch. Receives `LoraHighA–C`. Not MiniMax / Krea2 / LTX. |
| `clip_high` | CLIP | **Optional.** Wan high CLIP, and LoRA companion for MiniMax / image / video when those have no CLIP. |
| `model_low` | MODEL | **Optional.** Wan low-noise branch only (`LoraLowA–C`). MiniMax R2V belongs on `minimax_model`. |
| `clip_low` | CLIP | **Optional.** Pair with `model_low` for dual CLIP stacks. |
| `minimax_model` | MODEL | **Optional.** Singular MiniMax H3 UNET. Wire Lazy Model Switcher here. Receives `VideoModelLoraA–D`. |
| `image_model` | MODEL | **Optional.** Singular image model (Krea2, Z-Image, Flux, SDXL). Receives `ImageModelLoraA–D`. |
| `video_model` | MODEL | **Optional.** Singular video UNET (LTX 2.x). Receives `VideoModelLoraA–D`. |
| `subject` | dropdown | `.txt` under `ComfyUI/lazynodes/lazy_subject_scene_automation/SubjectFiles/` (recursive). Folder seed when **randomize** is ON. |
| `multisubject_refmod` | INT 0–3 | **0:** one subject, always load file LoRAs. **1:** one subject; skip that subject’s LoRAs if the file has **`[Refmod]`**. **2 / 3:** extra subject dropdowns (up to three characters). Randomize still applies `[Refmod]` LoRA skipping. |
| `min_subjects` | INT 1–3 | When **randomize** is ON and **`multisubject_refmod`** is 2 or 3: pick at least this many files from the selected subject’s folder (up to the refmod count). **2** with refmod **3** randomly picks 2 or 3. Hidden unless that combination is active. |
| `subject_2` / `subject_3` | dropdown | Extra subject `.txt` files. Shown when **`multisubject_refmod`** is 2 or 3. Ignored while randomize is ON (picks come from subject 1’s folder). Default `none`. |
| `scenario` | dropdown | First scenario `.txt` under `ComfyUI/lazynodes/lazy_subject_scene_automation/ScenarioFiles/` (recursive). |
| `scenario_2` | dropdown | Second scenario `.txt` (same folder and format). Default `none`. Adds up to three more LoRA slots (A/B/C) after scenario 1. |
| `scenario_2_high_strength` | FLOAT | Overrides `[LoraHighA]` **model** strength in scenario 2 live text (0–10, step 0.01). Sliders sit above the scenario 2 live editor. |
| `scenario_2_low_strength` | FLOAT | Overrides `[LoraLowA]` **model** strength in scenario 2 live text. Clip strengths in the file are unchanged. |
| `pass_subject_to_main_prompt` | BOOLEAN | As before. |
| `randomize_subject_in_directory` | BOOLEAN | **OFF** (default): use the selected `subject` / `subject_2` / `subject_3` dropdowns. **ON**: each queue randomly picks `.txt` file(s) from the **same folder** as the selected subject (e.g. select `cast/alice` → random pick among all files in `SubjectFiles/cast/`). Count is **`min_subjects`** through **`multisubject_refmod`** when that is 2 or 3. Reads from disk; ignores live subject panes. `[Refmod]` LoRA skipping still applies. |
| `video_length` | FLOAT | Clip duration in seconds (0–300, default **0** = skip). Replaces `[video_length]` in `prompt` / `prompt_override`, or appends a `[video_length]` block. Does not change `[Time]` (time of day). MiniMax template sets this to 8. Prompt Engineer keeps the block in the LLM user message. |
| `prepend_text` | STRING (optional, **socket only**) | Wired text prepended to the built prompt; empty if unconnected. |
| `post_text` | STRING (optional, **socket only**) | Wired text after the subject block; empty if unconnected. |
| `global_selector_input` | STRING (optional, **socket only**) | From [Lazy Global Selector](lazy-global-selector.md). Used as `[Workflow]` in the selector blob when subject/scenario files do not set `[Workflow]`. Does **not** switch model sockets. |

## Outputs

| Output | Notes |
|--------|--------|
| `prompt` | Readable layout for preview nodes (newlines / blank lines; see below). |
| `model_high` / `model_low` | After merged LoRA stacks. |
| `keywords` | `KeywordA/B/C` from subject files (1 then 2 then 3), then scenario 1, then scenario 2, joined with `", "` and a trailing `", "` when non-empty. |
| `clip_high` / `clip_low` | After the same stacks as the paired model outputs. |
| `subject_description` | Raw subject-side description only (no prepend/post). Multiple subjects are joined with a blank line. |
| `prompt_override` | **Prompt override output** — text from scenario `[Prompt]` blocks (scenario 1 and/or 2). Empty when files use `[desciption]` instead. Wire to LazyPrompt **prompt_override_input**. Not included in the main `prompt` output. |
| `selector` | MiniMax / media routing blob for [Lazy MiniMax All-in-One](lazy-minimax-all-in-one.md). Built from `[Workflow]`, `[ReferenceImage1]`–`[ReferenceImage5]`, `[AudioReference]` in subject + scenario files (see below). Empty when those tags are absent (unless `global_selector_input` supplies a mode). |
| `minimax_model` | After `VideoModelLoraA–D` (passthrough if unwired). |
| `image_model` | After `ImageModelLoraA–D`. |
| `video_model` | After `VideoModelLoraA–D`. |
| `refmod` | Tagged blob of up to three `[Refmod1]`–`[Refmod3]` rows from subject files. Empty when no `[Refmod]` tags. Wire to [Lazy-refmod-split](lazy-refmod-split.md). |

## LoRA application order

On each branch, LoRAs are applied in order:

1. **Subject 1** (then **subject 2**, then **subject 3** when those slots are active): slot A → slot B → slot C (`LoraHighA` / `LoraLowA` through `LoraHighC` / `LoraLowC` in each subject file). When **`multisubject_refmod` ≥ 1** and that file has a non-bypass **`[Refmod]`**, that subject’s LoRAs (Wan / Image / Video) are skipped.
2. **Scenario 1:** slot A → slot B → slot C (same tag names in the first scenario file).
3. **Scenario 2:** slot A → slot B → slot C from the second scenario file when **`scenario_2`** is not `none` (up to six scenario LoRA sets total).

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
| `ImageModelLoraA` … `ImageModelLoraD` | Applied to **`image_model`** only. Bypass / omitted = skip. |
| `VideoModelLoraA` … `VideoModelLoraD` | Applied to **`minimax_model`** and/or **`video_model`**. Not applied to Wan High/Low. |
| `KeywordA` / `KeywordB` / `KeywordC` | Merged into `keywords` output. |
| `Workflow` | Optional. MiniMax mode hint: `T2V` / `T2VA` / `I2V` / `I2VA` / `FL2V` / `R2V` (aliases normalized). Emitted on **`selector`**. Place **before** description / Prompt. |
| `ReferenceImage1` … `ReferenceImage5` | Optional paths under ComfyUI `input/` (e.g. `folder/image.png`). Emitted on **`selector`**. |
| `AudioReference` | Optional audio path under `input/`. Emitted on **`selector`**. |
| `description` or `desciption` | Subject description in the final `prompt`. |
| `Refmod` | Optional MiniMax H3 reference mod for [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod) **Load H3 RefMods**. Tag line: `[Refmod][strength][copies]`. Body is the dropdown name (e.g. `vanellope_example`); `.safetensors` is stripped if present. Strength defaults to **1.0**; copies (third bracket) defaults to **1** (range 1–10). Example: `ComfyUI/lazynodes/lazy_subject_scene_automation/SubjectFiles/Refmod example.txt`. When **`multisubject_refmod` ≥ 1**, a present `[Refmod]` also **skips that subject’s LoRAs**. |

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

MiniMax H3 RefMod (name matches a **Load H3 RefMods** dropdown; set **`multisubject_refmod`** to 1+ to skip LoRAs when this tag is present):

```text
[LoraHighA]
bypass
[LoraLowA]
bypass
[Refmod][1.0]
vanellope_example
[desciption]
a candy racer with black hair in pigtails
```

Optional third bracket is **copies** (integer 1–10, default 1): `[Refmod][0.85][2]`.

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
| `ImageModelLoraA` … `ImageModelLoraD` | Applied to **`image_model`**. |
| `VideoModelLoraA` … `VideoModelLoraD` | Applied to **`minimax_model`** and/or **`video_model`**. |
| `KeywordA` / `KeywordB` / `KeywordC` | Appended after subject keywords in `keywords`. |
| `Workflow` / `ReferenceImage1`–`5` / `AudioReference` | Same MiniMax selector tags as subject files. Merged into **`selector`** (scenario non-empty values override subject; scenario 2 overrides scenario 1). |
| `description` or `desciption` | Scenario text; appears after the subject block in `prompt`. |
| `Prompt` | **Mutually exclusive with `description`/`desciption`.** Body is sent on **`prompt_override`** (for LazyPrompt LLM override), not in the main `prompt` output. If both tags exist, **`Prompt` wins**. Multiline bodies include all lines until the next **known** `[Tag]` section (lines with other `[brackets]` stay in the prompt). |

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

### Random prompt choices `{a|b|c}`

In **scenario** files only (v2 tagged bodies: **`[desciption]`**, **`[Prompt]`**, **`KeywordA`**–**`KeywordC`**), you can embed **random alternatives** using curly braces and pipe separators:

```text
[desciption]
A blond girl walks to the {left|right} side of the frame
```

```text
[Prompt]
Cinematic shot, camera pans {left|right}, {morning|evening} light
```

**Behavior:**

- Each `{option1|option2|…}` group picks **one** alternative at **queue time** (new random pick every run).
- Expansion uses **`secrets`** (not Python’s global `random`) so picks are not locked to the ComfyUI workflow seed.
- When scenario text contains `{a|b}` groups, **`IS_CHANGED`** busts output cache so ComfyUI re-runs the node each queue (otherwise cached output could repeat the same pick).
- Options are **trimmed** — multiline groups like `{true|false|1|2}` on separate lines work.
- Multiple groups in the same line are expanded independently (`{left|right} and {up|down}` → four possible outcomes).
- Innermost `{…}` groups resolve first, so nested patterns like `{wide|{medium|tight}}` work.
- LoRA path lines are **not** expanded (only description, Prompt, and keyword text after parsing).
- Live editor panes and **Save edits** keep the **source** text with `{…}`; expansion happens in **`run`**, not in **`read_pair`** preview loads.

This replaces an external random-prompt handler for scenario-side variation. Wire **`[Prompt]`** with random groups to **`prompt_override`** → LazyPrompt **`prompt_override_input`** when using the LLM path.

### MiniMax selector example

Place new tags **before** `[desciption]` / `[Prompt]`:

```text
[Workflow]
R2V
[ReferenceImage1]
chars/hero.png
[ReferenceImage2]
style/mood.png
[AudioReference]
sfx/voice.wav
[desciption]
A blond girl jumps on a trampoline
```

Wire **`selector`** → [Lazy MiniMax All-in-One](lazy-minimax-all-in-one.md) **`selector`**.

MiniMax / LTX LoRAs (applied to **`minimax_model`** / **`video_model`**, not Wan High/Low):

```text
[VideoModelLoraA][1.0]
rtx\upscale.safetensors
[VideoModelLoraB]
bypass
[desciption]
A blond girl jumps on a trampoline at [Time]
```

Put **`[video_length]`** in **`[Prompt]`** (or the main prompt) where the clip duration should appear. SAS replaces that token from the **`video_length`** widget. **`[Time]`** stays as time of day.

---

## Live editors, scenario 2 strength, and HTTP API

The extension **`js/lazy_subject_scene_live.js`** (loaded via the pack `WEB_DIRECTORY`) adds the on-node UI below the dropdowns.

### On-node layout (top → bottom)

1. **Subject file (live — used on queue)** — editable textarea. **Subject 2 / 3** panes appear when **`multisubject_refmod`** is 2 or 3 and randomize is off.
2. **Scenario file (live — used on queue)** — editable textarea.
3. **`scenario_2_high_strength`** / **`scenario_2_low_strength`** — standard ComfyUI float widgets (only active when **`scenario_2`** ≠ `none`). Placed above the scenario 2 pane.
4. **Scenario 2 file (live — used on queue)** — editable textarea.
5. **Save edits** — one button; writes all applicable panes to disk.

### Queue vs disk

- On **queue**, the extension syncs live panes into hidden widgets via **`beforeQueuePrompt`** (and a `queuePrompt` fallback). Any pane with text is marked **live** for that run.
- After you **edit a pane**, that side’s live buffer is used on **queue**, even if you have not saved to disk. Non-empty synced buffers are also preferred over disk when the pane was loaded but not manually edited.
- Changing a **dropdown** reloads that pane from disk via **`read_pair`** (unless the workflow already stored live text).
- **`Save edits`** POSTs only non-empty panes for paths that are not `none`; empty panes are skipped.
- **`{a|b|c}` random groups** in scenario text are expanded when the graph **runs**, not when live panes reload from disk.

### Scenario 2 strength sliders

- On load (or when **`scenario_2`** changes), sliders read **model** strength from the scenario 2 file’s **`[LoraHighA]`** and **`[LoraLowA]`** tag lines (default **1.0** if omitted).
- Moving a slider rewrites the corresponding tag line in the **scenario 2 live** textarea (clip strength on that line is unchanged).
- At execution, the server applies the same overrides to scenario 2 text before parsing LoRAs.

Only **scenario 2** has these sliders (extra scenario layer); subject and scenario 1 use strengths from the file or live text as written.

### Hidden sync widgets

`subject_live`, `subject_2_live`, `subject_3_live`, `scenario_live`, `scenario_2_live`, and matching `*_use_live` flags are hidden on the node but stored in the workflow JSON for queue serialization.

| Method | Path | Body / notes |
|--------|------|----------------|
| `POST` | `/vsaan212/lazy-subject-scene/read_pair` | JSON `subject`, `scenario`, optional `scenario_2`, `subject_2`, `subject_3` → file texts + optional `*_error` fields. |
| `POST` | `/vsaan212/lazy-subject-scene/save_live_files` | JSON paths + `subject_text` / `subject_2_text` / `subject_3_text` / `scenario_text` / `scenario_2_text` (only non-empty fields are written). |

---

## Prompt output layout

The node builds:

1. `prepend_text` plus a **newline** when prepend is non-empty.  
2. Subject `description`.  
3. A **blank line**, then `post_text` (when post is non-empty and something precedes it).  
4. A **blank line**, then scenario descriptions (scenario 1 and scenario 2 joined with a blank line when both have text).

Use **`none.txt`** (or equivalent bypass-only files) in the dropdowns when you want no LoRAs or empty descriptions from that side.

## See also

- [Optional Switch LoRA](optional-switch-lora.md) — same bypass/path semantics for a single LoRA step.
- [Subject Selector](subject-selector.md) / [Scenario Selector](scenario-selector.md) — load raw text only from different folders.
- [Lazy-refmod-split](lazy-refmod-split.md) — fan `refmod` into Load H3 RefMods `mod_#` / `strength_#` / `copies_#`.
