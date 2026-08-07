---
title: Wire up a local LLM
index: 40
---

# How to wire up a local LLM

LazyPrompt can enhance short ideas into long MiniMax prompts. You choose a **backend** on **LazyPrompt — Prompt Engineer** with the **`model`** dropdown.

## Option A — LM Studio (easiest for most people)

Best when you want a modern chat model on your PC and optional **vision** (the model can “see” the first frame).

### 1. Install and start LM Studio

1. Install [LM Studio](https://lmstudio.ai/).  
2. Download a chat model that fits your VRAM (see **What local LLMs are supported**).  
3. Load the model.  
4. Start the **local server** (default `http://127.0.0.1:1234`).  
5. Copy the **exact model id** shown in LM Studio.

### 2. Set the Comfy node

On **LazyPrompt — Prompt Engineer**:

| Setting | Value |
|---------|--------|
| **model** | `LM Studio (API)` |
| **lm_studio_model** | Exact id from LM Studio |
| **target_model** | Match your mode, e.g. `MiniMax H3 I2V` / `FL2V` / `R2V` |
| **bypass** | OFF (ON = skip the LLM and pass text through) |
| **creativity** | Start around **0.5–0.7** (max **1.0**) |
| **max_output_tokens** | Start **900**; raise for longer cinematic prompts |
| **video_length** | Match your clip length in seconds |

### 3. Wire the text (and optional image)

1. Type a short idea in **`user_input`**.  
2. Optional: wire Subject automation **`subject_description`** → **`character`**.  
3. Optional: wire **`prompt_override`** → **`prompt_override_input`**.  
4. For vision: wire your first-frame Image Loader → Prompt Engineer **`first_frame`**, and wire Global Selector → **`global_selector_input`**.  
5. Take **`PROMPT`** (or the path your graph already uses) into MiniMax / text encode.

LM Studio **0.4+** uses `/api/v1/chat`. Older builds fall back to `/v1/chat/completions` automatically.

### Common LM Studio mistakes

- Server not running → connection errors in the Comfy console.  
- Model id typo → 404 / “model not found”.  
- Creativity above **1.0** → LM Studio may reject the request (the node clamps this).

---

## Option B — Built-in Hugging Face models (no LM Studio)

On Prompt Engineer, set **model** to:

- **`8B - NeuralDaredevil (High Quality)`** — better quality, more VRAM  
- **`3B - Llama-3.2 Abliterated (Low VRAM)`** — lighter  

Optional:

- Point **`local_path_8b`** / **`local_path_3b`** at a downloaded snapshot folder.  
- Turn **`offline_mode`** ON after the model is cached.  
- **`keep_model_loaded`** ON keeps it in VRAM between runs; use **LazyPrompt — Unload local model** when finished.

**Important:** these local HF backends **do not see images**. If you need a caption of the frame, run **LazyPrompt — Vision Describe** on the image and wire its text into **`scene_context`**.

---

## Option C — TextGenerate (CLIP)

1. Set **model** to **`TextGenerate (CLIP)`**.  
2. Wire an LLM-capable **CLIP** (for example a Qwen text/LLM CLIP loader) into the Prompt Engineer **`clip`** input.  
3. Use this when you already run an LLM inside Comfy’s CLIP stack.

---

## Skipping the LLM entirely

Turn **`bypass`** ON on Prompt Engineer. Your **`user_input`** (or override text) passes through unchanged. Useful for testing images/models without waiting on the LLM.
