# LazyPrompt

Three related nodes for LLM-assisted prompting inside ComfyUI.

| Registry name | Menu title |
|---------------|------------|
| `LazyPromptEngineer` | LazyPrompt — Prompt Engineer |
| `LazyPromptVisionDescribe` | LazyPrompt — Vision Describe |
| `LazyPromptUnloadModel` | LazyPrompt — Unload local model |

**Credits:** upstream design from LTX2EasyPrompt-LD and Gemma4Prompt (MIT); see the main [README](../../README.md#credits).

## LazyPrompt — Prompt Engineer

**Purpose:** Expand a short user idea into a long-form prompt tuned for a **target model** (LTX Video, Wan, Flux, SDXL, Pony, SD 1.5).

### Workflow wiring

1. Choose **`target_model`** so the correct system prompt and pacing rules apply (video vs image token budgets differ).
2. Set **`model`** to either a **local Hugging Face** Gemma-style LLM (8B/3B paths) or **LM Studio (API)**.
3. Enter your idea in **`user_input`** (and optional **`character`**, **`lora_triggers`**, **`environment`** preset).
4. Optional **`scene_context`** — connect text from **Vision Describe** or any frame/scene description.
5. Optional **`image`** — **LM Studio only**, when using a **vision** model in LM Studio: start frame or reference is sent as JPEG in an OpenAI-style chat (same general pattern as ComfyExpo LM Studio nodes). **Ignored** for local 8B/3B Transformers backends; use Vision Describe → `scene_context` instead.
6. **`bypass`** ON skips the LLM and passes **`user_input`** through (good for debugging graphs).
7. Outputs: **`PROMPT`** (use for encoding), **`PREVIEW`** (duplicate for UI), **`NEG_PROMPT`** (where the stack splits negatives for SDXL/Pony/SD1.5 tag formats).

### Operational tips

- Match **frame_count / fps** to your video node so length hints align with clip duration.
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
`Load Image` (start frame) → **Prompt Engineer** `image` pin + LM Studio model → expanded prompt → video model conditioning.

**Static library only**  
Use [Lazy Prompt Saver](lazy-prompt-saver.md) instead of Prompt Engineer when you do not need an LLM.

## See also

- Main README [Credits](../../README.md#credits) for upstream authors.
- [Text Split](text-split.md) if you need to split a long `PROMPT` across multiple encoders.
