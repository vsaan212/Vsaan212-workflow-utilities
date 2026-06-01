# Vsaan212-workflow-utilities

ComfyUI custom nodes: selectors, dual-stack subject/scene automation, text utilities, optional LoRA bypass, prompt library, and **LazyPrompt** (multi-target prompt engineer + optional vision). MIT licensed.

## Nodes (summary)

| Node | What it does | Full guide |
|------|----------------|------------|
| **Subject Selector** | Load `.txt` from `subjectselector/SubjectFiles/` (recursive). | [docs/nodes/subject-selector.md](docs/nodes/subject-selector.md) |
| **Scenario Selector** | Load `.txt` from `scenarioselector/ScenarioFiles/` (recursive). | [docs/nodes/scenario-selector.md](docs/nodes/scenario-selector.md) |
| **Lazy-subject-and-scene-automation** | One node: **one subject** + **two scenario** files (up to 6 scenario LoRA sets), Wan-style high/low stacks, `prompt` + `keywords`. **Live editors** on the node (queue uses pane text, not disk); **Save edits** to `.txt`; **scenario 2 strength** sliders override `[LoraHighA]` / `[LoraLowA]` model strength. Uses **`lazy_subject_scene_automation/SubjectFiles`** and **`…/ScenarioFiles`**. | [docs/nodes/lazy-subject-scene-automation.md](docs/nodes/lazy-subject-scene-automation.md) |
| **Text Split** | Split by separator, regex, or **tagged format** (`[Tag]` headers). **Auto-detects** v2 subject/scenario files when the first line is `[LoraHighA]`; otherwise **`tagged_format`** or separator `#` for legacy graphs. | [docs/nodes/text-split.md](docs/nodes/text-split.md) |
| **Optional Switch LoRA** | Apply a LoRA or pass through when path is `bypass` / empty. | [docs/nodes/optional-switch-lora.md](docs/nodes/optional-switch-lora.md) |
| **Lazy Prompt Saver** | Save / clone / delete named prompts in `lazy_prompts.json`. | [docs/nodes/lazy-prompt-saver.md](docs/nodes/lazy-prompt-saver.md) |
| **LazyPrompt** | Prompt Engineer (LTX / Wan / Flux / SDXL / Pony / SD 1.5), Vision Describe (Qwen2.5-VL), Unload local model. | [docs/nodes/lazyprompt.md](docs/nodes/lazyprompt.md) |

**Documentation index:** [docs/README.md](docs/README.md)

## Installation

### Via Comfy Registry (recommended)
Search for **`vsaan212/Vsaan212-workflow-utilities`** in the ComfyUI Manager and click **Install**.

### Manual (development)
Clone into your Comfy install:

<ComfyUI root>/
└─ custom_nodes/
└─ vsaan212_workflow_utilities/ # this repo's custom_nodes/* contents

Restart ComfyUI.

## Folder layout & auto-creation

On first load the pack creates missing folders as needed.

**Standalone selectors**

```
custom_nodes/vsaan212_workflow_utilities/
├─ scenarioselector/ScenarioFiles/
└─ subjectselector/SubjectFiles/
```

**Lazy-subject-and-scene-automation** (separate library)

```
custom_nodes/vsaan212_workflow_utilities/
└─ lazy_subject_scene_automation/
   ├─ ScenarioFiles/
   └─ SubjectFiles/
```

Put `.txt` files under the folder that matches the node you use. Dropdowns show **relative paths without `.txt`** (POSIX-style); nested subfolders are supported.

**Subject & scenario file formats (selectors + Text Split)**

- **Tagged (current):** sections start with a `[Tag]` line (e.g. `[LoraHighA]`, `[desciption]`), body on following lines until the next tag. Shipped examples: `Bypass and format example.txt`, `none.txt`.
- **Legacy:** sections separated by a line containing only `#` (blank line, `#`, blank line).

**Lazy-subject-and-scene-automation** parses tagged files internally. The browser extension **`js/lazy_subject_scene_live.js`** adds editable **subject / scenario / scenario 2** panes, **Save edits**, and **scenario 2 high/low strength** sliders (see [lazy-subject-scene-automation.md](docs/nodes/lazy-subject-scene-automation.md)). For **Subject Selector** / **Scenario Selector** → **Text Split**, v2 files (first line `[LoraHighA]`) split automatically; legacy `#` files use separator `#` unless you force **`tagged_format` ON**. Text Split details: [text-split.md](docs/nodes/text-split.md).

## Python dependencies

Install from `requirements.txt` if your ComfyUI environment is missing anything (`transformers`, `torch`, `qwen-vl-utils`, `Pillow`, `numpy`, etc.).

## Credits

**LazyPrompt** in this pack reuses and adapts MIT-licensed community work. Thank you to the original authors:

- **LoRa-Daddy** — *LTX-2 Easy Prompt* (**LTX2EasyPrompt-LD**): cinematic LTX-style expansion, Qwen2.5-VL → `scene_context`, negative hints, LoRA triggers, dialogue / bypass, frame pacing, local Hugging Face + **LM Studio** patterns, output cleaning. LazyPrompt’s **Prompt Engineer** and **Vision Describe** descend from that design.
- **seanhan19911990-source** — MIT-licensed **LTX2EasyPrompt-LD** tree (copyright in that project’s `LICENSE`); original upstream listing may no longer be on GitHub.
- **Brojakhoeman** — MIT **Gemma4Prompt** (copyright in that project’s `LICENSE`): per-target system prompts (LTX 2.3, Wan 2.2, Flux.1, SDXL, Pony XL, SD 1.5), LTX screenplay variant, and **environment presets** merged into LazyPrompt.

**vsaan212** maintains this integrated repository (selectors, lazy subject/scene automation, Lazy Prompt Saver, LazyPrompt merge, and packaging) separately from those upstreams.

## Troubleshooting

- **New `.txt` files not in dropdown:** Press **`R`** in ComfyUI or recreate the node. Lazy-subject-and-scene-automation also refreshes via `/vsaan212/lazy-subject-scene/…` when the node is created.
- **Same filename in two folders:** Use the full relative path in the dropdown.
- **Line endings:** Nodes normalize `\r\n` / `\r` to `\n`.

### Example workflow screenshot (depricated, the new node removes the need for this)
<img width="2409" height="1254" alt="image" src="https://github.com/user-attachments/assets/704942fe-796c-422b-888b-3ebab1fd838c" />

## License
MIT (see `LICENSE`)
