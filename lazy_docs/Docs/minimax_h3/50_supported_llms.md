---
title: What local LLMs are supported
index: 50
---

# What local LLMs are supported

“Supported” here means: **LazyPrompt can call it**. Quality still depends on the model you pick.

## Prompt Engineer backends (built into the node)

| Backend | What it is | Vision (sees images)? | Notes |
|---------|------------|------------------------|-------|
| **LM Studio (API)** | Any model you load in LM Studio | **Yes**, if the loaded model is a vision/chat multimodal model | Recommended default. Exact model id required. |
| **8B NeuralDaredevil** | Local Hugging Face checkpoint | **No** | Higher quality text; more VRAM. |
| **3B Llama-3.2 Abliterated** | Local Hugging Face checkpoint | **No** | Lower VRAM. |
| **TextGenerate (CLIP)** | Comfy core GenerateText via wired CLIP/LLM | Depends on the CLIP/LLM | Must wire the **`clip`** input. |

## Good LM Studio choices (practical)

These are **examples**, not a hard whitelist. Prefer models that:

- Follow instructions well  
- Handle long prompts  
- (For I2V/FL2V/R2V with images) support **vision** if you wire `first_frame`

Common categories people use successfully:

- Mid-size instruct models (7B–14B class) for text-only enhancement  
- Vision-language instruct models when you want the LLM to respect the start frame  
- Larger models if you have the VRAM and want richer cinematic wording  

Always copy the **exact** name LM Studio shows into **`lm_studio_model`**.

## Vision Describe (separate node)

**LazyPrompt — Vision Describe** is not the Prompt Engineer backend. It runs **Qwen2.5-VL** (3B or 7B variants) locally to turn an image into caption text for **`scene_context`**.

Use it when:

- You use the **8B/3B HF** Prompt Engineer backends (no image), or  
- You want a dedicated caption before enhancement  

Weights cache under your Hugging Face hub cache (Windows: `%USERPROFILE%\.cache\huggingface\hub\`).

## MiniMax “target_model” skills (not LLMs)

The **`target_model`** dropdown is **not** the LLM. It picks the **writing style template** (Model_Skills), for example:

- MiniMax H3 I2V  
- MiniMax H3 FL2V  
- MiniMax H3 R2V  
- Plus other packs (LTX, Wan, Flux, SDXL, …)

Match **`target_model`** to how you are generating video so the LLM formats the prompt correctly.

## Quick pick guide

| Your situation | Use |
|----------------|-----|
| Want simplest setup + optional image understanding | **LM Studio (API)** + vision model |
| No LM Studio, okay VRAM | **8B NeuralDaredevil** + Vision Describe for frames |
| Tight VRAM | **3B Llama** + Vision Describe |
| Already have Qwen/LLM CLIP in Comfy | **TextGenerate (CLIP)** |
| Just testing the video model | Prompt Engineer **bypass** ON |
