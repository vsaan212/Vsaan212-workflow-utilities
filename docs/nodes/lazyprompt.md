# LazyPrompt

Three related nodes for LLM-assisted prompting inside ComfyUI.

| Registry name | Menu title |
|---------------|------------|
| `LazyPromptEngineer` | LazyPrompt — Prompt Engineer |
| `LazyPromptVisionDescribe` | LazyPrompt — Vision Describe |
| `LazyPromptUnloadModel` | LazyPrompt — Unload local model |

**Credits:** upstream design from LTX2EasyPrompt-LD and Gemma4Prompt (MIT); see the main [README](../../README.md#credits).

**Deep dive:** [how prompt enhancement and `system_prompt` override work](lazyprompt-prompt-enhancement.md).

## LazyPrompt — Prompt Engineer

**Purpose:** Expand a short user idea into a long-form prompt tuned for a **target skill** (LTX Video, Wan, **MiniMax H3 TR2V / I2V / FL2V / R2V**, Flux, SDXL, Pony, SD 1.5, plus Dialog / Screenplay variants).

Backends: local HF (8B/3B), **LM Studio (API)**, or **TextGenerate (CLIP)** — Comfy core Generate Text via a wired LLM-capable CLIP (e.g. Qwen). Wire `clip` when using that backend; gated `first_frame` is passed as vision when present.

### Workflow wiring

1. Choose **`target_model`** so the correct **Model_Skills** system template applies (**`None`** = no default template; optional minimal mode with override — see [lazyprompt-prompt-enhancement.md](lazyprompt-prompt-enhancement.md)). Skills are loaded from **`lazyprompt/Model_Skills/*.md`** (restart or **R** after edits). People, timeline, duration, and content-tone rules live in the skill file. Dialog / Screenplay are separate dropdown entries.
2. Set **`model`** to either a **local Hugging Face** Gemma-style LLM (8B/3B paths) or **LM Studio (API)**.
3. Enter your idea in **`user_input`** (prompt to be enhanced). Wire **`character`** ← **`subject_description`** from **Lazy-subject-and-scene-automation** so subject **`[desciption]`** always reaches the LLM (including when **`prompt_override_input`** is set). Optional **`lora_triggers`**, **`environment`** preset.
4. Optional **`scene_context`** — connect text from **Vision Describe** or any frame/scene description.
5. Optional **`prompt_override_input`** — when wired/non-empty, **replaces `user_input`** for the LLM request (LM Studio API and local HF). Typical source: **`prompt_override`** from **Lazy-subject-and-scene-automation** when the scenario file uses a **`[Prompt]`** block instead of **`[desciption]`**.
6. Optional **`user_instructions`** — filled into `***UserPrompt***` in the skill and copied into the user message as locked scene facts (empty = that skill section is omitted).
7. Optional media — **`first_frame`** (legacy alias **`image`**), **`last_frame`**, **`reference_image_1`…`5`**, **`reference_audio`**. Gate with **`global_selector_input`**. **`SAS_automation_selector_input`**: mode from `[Workflow]` always applies. Disk `[ReferenceImageN]` / `[AudioReference]` overlay matching slots only (typically **`reference_image_1`** and **`reference_audio`**); wired **`reference_image_2`…`5`** stay. A Workflow-only SAS blob keeps all sockets. **LM Studio vision**: I2V sends the gated first frame; FL2V sends first+last; R2V sends all connected **`reference_image_1`…`5`** (up to 5, labeled `<Picture N>` by socket index). Local HF backends ignore images — use Vision Describe → `scene_context`.
8. **`bypass`** ON skips the LLM and passes the effective user text through (override if connected, else **`user_input`**).
9. Optional **`model_high`** / **`clip_high`** / **`model_low`** / **`clip_low`** — Wan dual-stack from [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) (or a checkpoint) for Prompt **`[LoraH]`** / **`[LoraL]`**. Optional **`lora_model`** / **`lora_clip`** — singular MiniMax / LTX / image model for Prompt **`[Lora1]`**–**`[Lora5]`** (if **`lora_clip`** is empty, **`clip_high`** is the companion). After the LLM (or bypass), those tags are loaded then **stripped** from **`PROMPT`** / **`PREVIEW`**. Empty / `bypass` paths are ignored. File-slot LoRAs (`[LoraHighA]`, `[VideoModelLoraA]`, etc.) stay on the automation node.
10. Outputs: **`PROMPT`**, **`PREVIEW`**, **`NEG_PROMPT`**, **`selector_Out`**, gated media, plus **`model_high`** / **`model_low`** / **`clip_high`** / **`clip_low`** / **`lora_model`** / **`lora_clip`** (passthrough when unwired or no matching Prompt LoRA blocks).

### Prompt dynamic LoRA tags

Use closed tags in the Prompt / LLM output (not description). **Up to five** numbered LoRAs plus Wan high/low.

```text
[LoraH]path[/LoraH]
[LoraL[0.8]]path[/LoraL]
[Lora1[0.5]]path[/Lora1]
[Lora2]path[/Lora2]
```

| Tag | Stack | How many |
|-----|--------|----------|
| `[LoraH]` / `[LoraL]` | PE **`model_high`** / **`model_low`** (Wan) | One each (duplicates of the same path+strength are collapsed) |
| `[Lora1]` … `[Lora5]` | PE **`lora_model`** (MiniMax / LTX / Flux / SDXL) | Five slots, applied in order 1→5 |

Strength on the opening tag (same idea as SAS `[LoraHighA][0.85][1.0]`):

- `[Lora1]path[/Lora1]` — model **1.0**, clip **1.0**
- `[Lora1[0.5]]path[/Lora1]` — model **0.5**, clip **1.0**
- `[Lora1[0.5][0.8]]path[/Lora1]` — model **0.5**, clip **0.8**

Closing tag case does not matter (`[/lora1]` is fine). Empty or `bypass` paths are ignored.

Wire **`lora_model`** from SAS **`minimax_model`**, **`video_model`**, or **`image_model`**, then use PE’s **`lora_model`** output downstream. **`lora_clip`** is optional; **`clip_high`** is used if it is empty.

Tell the LLM (via **`user_instructions`** or **`system_prompt`**) to emit these when it picks a LoRA. Authored tags in scenario **`[Prompt]`** / **`prompt_override_input`** are collected even if the LLM drops them; only the final **`PROMPT`** text is stripped. Example scenario file: `ComfyUI/lazynodes/lazy_subject_scene_automation/ScenarioFiles/Prompt dynamic Lora example.txt`.

### Operational tips

- Match **`video_length`** (seconds) to your clip; it fills the skill’s `***VideoLength***` slot unless SAS already put **`[video_length]`** in the user/override text (that value wins, and the tag is kept in the user message). Image skills strip that slot.
- **`creativity`** is temperature **0.1–1.0** (step **0.1**); keep ≤ **1.0** for LM Studio.
- **`max_output_tokens`** — hard cap for generated completion length (HF / LM Studio). Default **900**. Raise for longer cinematic prompts.
- **`keep_model_loaded`** saves reload time at the cost of VRAM; use **Unload local model** when done.
- **`offline_mode`** + **`local_path`** for HF models when you do not want hub access.

---

## LazyPrompt — Vision Describe

**Purpose:** Run **Qwen2.5-VL** locally to caption an **`IMAGE`** into text for **`scene_context`** on Prompt Engineer (or any string input).

### Workflow wiring

1. Connect **`image`** from your load/VAE preview branch.
2. Pick **`model_name`** (3B or 7B variant); set **`offline_mode`** after weights are cached if needed.
3. Set **`local_path`** to a snapshot folder to pin a specific install (overrides the dropdown id).

### Where models are cached

- **Windows:** `%USERPROFILE%\.cache\huggingface\hub\` (folder names like `models--…--Qwen2.5-VL-…`).
- **Linux / macOS:** `~/.cache/huggingface/hub/`.

**Offline:** enable **`offline_mode`** only after download, or point **`local_path`** at the snapshot; otherwise first run may need network.

**Python:** `qwen-vl-utils` is required (see `requirements.txt`).

---

## LazyPrompt — Unload local model

**Purpose:** Free VRAM after **Prompt Engineer** was used with **`keep_model_loaded`** enabled.

Wire it after your generation branch (or run manually) when you no longer need the local HF LLM resident on the GPU.

---

## Typical graph shapes

**Image workflow (local LLM, no LM vision)**  
`Load Image` → **Vision Describe** → `scene_context` string → **Prompt Engineer** → CLIP / KSampler.

**Video + LM Studio vision**  
`Load Image` / Lazy Image Loader (start frame) → **Prompt Engineer** `first_frame` + LM Studio model → expanded prompt → video model conditioning. Wire [Lazy Global Selector](lazy-global-selector.md) so unused media sockets stay empty.

**Static library only**  
Use [Lazy Prompt Saver](lazy-prompt-saver.md) instead of Prompt Engineer when you do not need an LLM.

## See also

- Main README [Credits](../../README.md#credits) for upstream authors.
- [Text Split](text-split.md) if you need to split a long `PROMPT` across multiple encoders.
