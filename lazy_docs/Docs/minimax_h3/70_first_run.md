---
title: First-run checklist
index: 70
---

# First-run checklist

Use this once when the graph is new to you.

## 1. Models

- MiniMax text encoder / projector files in `models/text_encoders/`  
- `fl2va` diffusion model for T2V / I2V / FL2V  
- `ref2va` diffusion model if you will use R2V  
- Wire both UNETs into **Lazy Model Switcher** if your graph has that node  

## 2. Mode and image

1. Global Selector → **I2V**  
2. First-frame Image Loader: load a clear image; crop/resize if your graph expects it  
3. Leave other loaders alone (they should gate themselves)  

## 3. Subject / scene (optional but useful)

1. Open Subject + Scene automation  
2. Pick a subject (or `none`) and a scenario (or `none`)  
3. Skim the live panes; edit if you want  
4. Wire **`subject_description`** → Prompt Engineer **`character`** if using LazyPrompt  

## 4. LazyPrompt

1. **target_model** = MiniMax skill matching your mode (I2V for this checklist)  
2. **model** = LM Studio (API) *or* 8B/3B *or* bypass for a dry run  
3. If LM Studio: server running + **lm_studio_model** filled  
4. Short idea in **user_input**  
5. **video_length** matches the clip  

## 5. Queue

1. Queue once  
2. If the LLM step fails, set Prompt Engineer **bypass** ON and queue again to test the video path alone  
3. When happy, turn bypass OFF and refine the short idea  

## 6. Read the docs inside Comfy

On **Lazy Docs**, set Folder to **`local_minimax_h3`** for this beginner pack, or **`minimax_h3`** for the shorter shipped notes.
