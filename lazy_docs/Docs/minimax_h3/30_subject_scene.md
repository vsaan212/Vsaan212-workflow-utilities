---
title: Subject and Scene selectors
index: 30
---

# Subject and Scene selectors (layman version)

There are two related ideas in this pack:

1. **Standalone Subject Selector / Scenario Selector** — each loads one `.txt` file and outputs text.  
2. **Lazy Subject + Scene Automation** (the big node) — picks **one to three subjects** + **one or two scenarios**, applies LoRAs (or MiniMax RefMods), and builds prompt pieces for MiniMax / LazyPrompt.

For the MiniMax all-in-one graph you almost always use the **automation** node.

## Where the files live

| Node | Folder |
|------|--------|
| Lazy Subject + Scene Automation | `ComfyUI/lazynodes/lazy_subject_scene_automation/SubjectFiles/` and `…/ScenarioFiles/` |
| Standalone Subject Selector | `ComfyUI/lazynodes/subjectselector/SubjectFiles/` |
| Standalone Scenario Selector | `ComfyUI/lazynodes/scenarioselector/ScenarioFiles/` |

These folders are **separate** (all under `ComfyUI/lazynodes/`). Copy a file if you want the same character in both places. Pack updates do not wipe `lazynodes/`.

## Mental model

- **Subject** = *who* (character, face LoRA, body LoRA, short description).  
- **Scenario / Scene** = *what happens* (outfit/action LoRAs, scene description, or a full `[Prompt]` block).  
- **Scenario 2** (optional) = a second scene file stacked on top (extra LoRAs / text).

Pick `none` when you want that side empty.

## What a file looks like (v2 tags)

Plain text. Sections start with a tag in square brackets:

```text
[LoraHighA]
my_character_face.safetensors
[LoraLowA]
bypass
[desciption]
A young woman with short black hair, green jacket, calm expression
```

Important words:

- **`bypass`** — skip that LoRA slot (case does not matter).  
- **`[desciption]`** — yes, that spelling is intentional in this pack. Body text under it is the character/scene description.  
- **`[Prompt]`** — optional full prompt block on a **scenario** file. When present, the automation node outputs it as **`prompt_override`** for LazyPrompt (it can replace your short `user_input`).  
  Inside **`[Prompt]`** (or LLM output), you may also use closed Prompt-side tags. **`[LoraH]path[/LoraH]`** / **`[LoraL]path[/LoraL]`** load on LazyPrompt **`model_high`** / **`model_low`**. **`[Lora1]`**–**`[Lora5]`** (optional strength `[Lora1[0.5]]path[/Lora1]`) load on **`lora_model`**. LazyPrompt applies them after the LLM and strips them from the text. Do **not** put those closed tags under **`[desciption]`** — file LoRAs stay on `[LoraHighA]` / `[VideoModelLoraA]` slots.  
- **`[KeywordA]`** etc. — short trigger words joined into the **keywords** output.

You can also write strengths on the tag line:

```text
[LoraHighA][0.85][1.0]
path\to\lora.safetensors
```

First number = model strength, second = clip strength (defaults to 1.0 if omitted).

## Live editors on the automation node

- The big text panes on the node are **live**.  
- **When you queue, Comfy uses the pane text**, not necessarily the file on disk.  
- Click **Save edits** to write the panes back to the selected `.txt` files.  
- After adding new files on disk, press **R** in ComfyUI to refresh dropdowns.

## How this wires into LazyPrompt

Typical MiniMax wiring:

1. Automation **`subject_description`** → Prompt Engineer **`character`**  
2. Automation **`prompt_override`** → Prompt Engineer **`prompt_override_input`** (only needed if your scene file uses `[Prompt]`)  
3. Automation **`model_high`** / **`clip_high`** (and optional low) → Prompt Engineer same sockets when using Prompt **`[LoraH]`** / **`[LoraL]`**; then use Prompt Engineer’s model/clip outs downstream  
4. Automation **`selector`** (or Prompt Engineer **`selector_Out`**) → MiniMax / Model Switcher  

## MiniMax-only tip

For MiniMax you often only wire **`model_high`** / **`clip_high`**. Leave the low model/clip sockets empty unless you are on a dual-stack (Wan-style) graph. Put LoRAs on High slots or set Low slots to `bypass`.

## Random subject in a folder

If **randomize subject in directory** is ON, each queue picks another `.txt` from the **same folder** as the selected subject (great for a `cast/` folder of characters). With **`multisubject_refmod`** set to **2** or **3**, **`min_subjects`** is the fewest characters to draw (for example **2** with refmod **3** picks 2 or 3 files).

## MiniMax H3 RefMods (multi-subject)

This is the multi-character identity path. Character LoRAs stacked on one graph **bleed** into each other. **[Luisacaotica](https://github.com/Luisacaotica)**’s [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod) RefMods keep each person on MiniMax H3’s native reference tokens instead — extract a mod per character, then load them here.

Install that pack. Put `.safetensors` mods where it looks (`models/refmods/` root; subfolders are not listed by Load H3 RefMods yet). In a subject file:

```text
[Refmod][1.0]
vanellope_example
[desciption]
a candy racer with black hair in pigtails
```

On the automation node:

1. Set **`multisubject_refmod`** to **1** (one character), **2**, or **3**. At **0**, LoRAs still load even if `[Refmod]` is in the file. At **1+**, `[Refmod]` **turns that subject’s LoRAs off** (identity comes from the RefMod instead).
2. For two or three named characters, pick **`subject_2`** / **`subject_3`**. Randomize uses the same folder as **subject**.
3. Wire **`refmod`** → **Lazy-refmod-split** → **Load H3 RefMods** (`mod_1` / `strength_1` / `copies_1`, and 2 / 3). Convert those loader widgets **to inputs**. Then **Apply H3 RefMod** as usual.

Load H3 RefMods validates **before** SAS runs, so a linked `mod_#` is empty at queue time. This pack patches that check so `'None' not found in mods/` does not block the queue. You do not need to copy their loader into this repo. Restart ComfyUI after updating.

Random subject picks also honor `[Refmod]` (skip LoRAs when mode is 1+).
