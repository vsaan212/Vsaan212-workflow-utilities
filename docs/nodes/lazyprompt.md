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

**Purpose:** Expand a short user idea into a long-form prompt tuned for a **target skill** (LTX Video, Wan, **MiniMax H3 I2V / FL2V / R2V**, Flux, SDXL, Pony, SD 1.5, plus Dialog / Screenplay variants).

Backends: local HF (8B/3B), **LM Studio (API)**, or **TextGenerate (CLIP)** — Comfy core Generate Text via a wired LLM-capable CLIP (e.g. Qwen). Wire `clip` when using that backend; gated `first_frame` is passed as vision when present.

### Workflow wiring

1. Choose **`target_model`** so the correct **Model_Skills** system template and pacing rules apply (**`None`** = no default template; optional minimal mode with override — see [lazyprompt-prompt-enhancement.md](lazyprompt-prompt-enhancement.md)). Skills are loaded from **`lazyprompt/Model_Skills/*.md`** (restart or **R** after edits). Video vs image budgets differ; Dialog / Screenplay are separate dropdown entries.
2. Set **`model`** to either a **local Hugging Face** Gemma-style LLM (8B/3B paths) or **LM Studio (API)**.
3. Enter your idea in **`user_input`** (prompt to be enhanced). Wire **`character`** ← **`subject_description`** from **Lazy-subject-and-scene-automation** so subject **`[desciption]`** always reaches the LLM (including when **`prompt_override_input`** is set). Optional **`lora_triggers`**, **`environment`** preset.
4. Optional **`scene_context`** — connect text from **Vision Describe** or any frame/scene description.
5. Optional **`prompt_override_input`** — when wired/non-empty, **replaces `user_input`** for the LLM request (LM Studio API and local HF). Typical source: **`prompt_override`** from **Lazy-subject-and-scene-automation** when the scenario file uses a **`[Prompt]`** block instead of **`[desciption]`**.
6. Optional **`user_instructions`** — temporary instructions injected into `***UserPrompt***` markers in the system prompt (empty = block omitted).
7. Optional media — **`first_frame`** (legacy alias **`image`**), **`last_frame`**, **`reference_image_1`…`5`**, **`reference_audio`**. Gate with **`global_selector_input`**. **`SAS_automation_selector_input`**: mode from `[Workflow]` always applies; direct image/audio sockets are ignored **only** when the blob has `[ReferenceImage*]` / `[AudioReference]` paths (loaded from disk). A Workflow-only SAS blob keeps wired Image Loader frames. **LM Studio vision**: I2V sends the gated first frame; FL2V sends first+last; R2V sends all connected **`reference_image_1`…`5`** (up to 5, labeled `<Picture N>` by socket index). Local HF backends ignore images — use Vision Describe → `scene_context`.
8. **`bypass`** ON skips the LLM and passes the effective user text through (override if connected, else **`user_input`**).
9. Optional **`model_high`** / **`clip_high`** / **`model_low`** / **`clip_low`** — wire from [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) (or a checkpoint) when using Prompt-side dynamic LoRAs. After the LLM (or bypass), any **`[LoraH]path[/LoraH]`** / **`[LoraL]path[/LoraL]`** blocks in the Prompt text are loaded onto the high/low stacks (strength **1.0**) and **stripped** from **`PROMPT`** / **`PREVIEW`** so the diffusion model never sees them. Empty / `bypass` paths are ignored. This is for scenario **`[Prompt]`** (and LLM output), not **`[desciption]`**. File-slot LoRAs (`[LoraHighA]`, etc.) stay on the automation node.
10. Outputs: **`PROMPT`**, **`PREVIEW`**, **`NEG_PROMPT`**, **`selector_Out`**, gated media, plus **`model_high`** / **`model_low`** / **`clip_high`** / **`clip_low`** (passthrough when unwired or no Prompt LoRA blocks).

### Prompt dynamic LoRA tags

Use closed tags in the Prompt / LLM output (not description):

```text
[LoraH]relative\or\absolute\lora.safetensors[/LoraH]
[LoraL]relative\or\absolute\lora.safetensors[/LoraL]
```

Tell the LLM (via **`user_instructions`** or **`system_prompt`**) to emit these when it picks a LoRA. Authored tags in scenario **`[Prompt]`** / **`prompt_override_input`** are collected even if the LLM drops them; only the final **`PROMPT`** text is stripped. Example scenario file: `lazy_subject_scene_automation/ScenarioFiles/Prompt dynamic Lora example.txt`.

### Operational tips

- Match **`video_length`** (seconds) to your clip so length hints align; image skills ignore it.
- **`creativity`** is temperature **0.1–1.0** (step **0.1**); keep ≤ **1.0** for LM Studio.
- **`max_output_tokens`** — hard cap for generated completion length (HF / LM Studio). Default **900**; pacing asks for **~⅓** of that (~300 tokens). Raise for longer cinematic prompts (e.g. **4500** max → ~**1500** target).
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
