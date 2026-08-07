---
title: What this workflow does
index: 10
---

# What this workflow does (plain English)

Think of the graph as a **video studio remote control**:

| Piece | Job |
|-------|-----|
| **Lazy Global Selector** | One dropdown: “text only”, “one start image”, “start+end images”, or “reference images”. Everything else follows this choice. |
| **Lazy Image Loader(s)** | Load your pictures. Only the ones that match the mode actually send an image; the others stay quiet. |
| **Subject + Scene automation** | Pick a **character** file and a **scene** file. They can add LoRAs (style/face) and short text descriptions. |
| **LazyPrompt** | Optional helper: turns a short idea into a long MiniMax-style prompt using an LLM. |
| **Lazy MiniMax All-in-One** | Builds the video conditioning the MiniMax model needs. |
| **Lazy Model Switcher** | Picks the right UNET (normal video vs reference video). |

## Modes in one sentence each

- **T2V** — Text to video. No images required.  
- **I2V** — One **first frame** image becomes the start of the clip.  
- **FL2V** — **First** and **last** frames; the video morphs between them.  
- **R2V** — Up to **five reference** images (and optional audio) to lock looks / identity.

## The happy path (first time)

1. Set Global Selector to **I2V**.  
2. Put a clear start frame on the **first-frame** Image Loader.  
3. Type a short idea into Prompt Engineer **user_input** (or use a Subject/Scene description).  
4. Queue the prompt.  

If something fails, open **Troubleshooting** in this same Docs folder.
