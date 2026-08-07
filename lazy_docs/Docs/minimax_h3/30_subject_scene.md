---
title: Subject and Scene selectors
index: 30
---

# Subject and Scene selectors (layman version)

There are two related ideas in this pack:

1. **Standalone Subject Selector / Scenario Selector** — each loads one `.txt` file and outputs text.  
2. **Lazy Subject + Scene Automation** (the big node) — picks **one subject** + **one or two scenarios**, applies LoRAs, and builds prompt pieces for MiniMax / LazyPrompt.

For the MiniMax all-in-one graph you almost always use the **automation** node.

## Where the files live

| Node | Folder |
|------|--------|
| Lazy Subject + Scene Automation | `lazy_subject_scene_automation/SubjectFiles/` and `…/ScenarioFiles/` |
| Standalone Subject Selector | `subjectselector/SubjectFiles/` |
| Standalone Scenario Selector | `scenarioselector/ScenarioFiles/` |

These folders are **separate**. Copy a file if you want the same character in both places.

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
3. Automation **`selector`** (or Prompt Engineer **`selector_Out`**) → MiniMax / Model Switcher  

## MiniMax-only tip

For MiniMax you often only wire **`model_high`** / **`clip_high`**. Leave the low model/clip sockets empty unless you are on a dual-stack (Wan-style) graph. Put LoRAs on High slots or set Low slots to `bypass`.

## Random subject in a folder

If **randomize subject in directory** is ON, each queue picks another `.txt` from the **same folder** as the selected subject (great for a `cast/` folder of characters).
