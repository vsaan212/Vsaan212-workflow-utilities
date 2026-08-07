---
title: Modes explained simply
index: 20
---

# Modes explained simply

Use **Lazy Global Selector** as your only mode switch. Do not mute half the graph by hand unless you are debugging.

## T2V — Text to video

- You write (or generate) a prompt.  
- No start image is required.  
- Image Loaders can stay connected; they simply emit nothing for this mode.

## I2V — Image to video (most common starter)

- Load **one** clear first frame (face and body visible if that matters).  
- The prompt describes **what happens next**, not a full caption of the still photo.  
- Prefer a sensible resolution (often ~768 on the short edge, or the pack’s megapixel resize).

## FL2V — First + last frame

- Load a **start** image and an **end** image.  
- Prompt should describe the journey between them (camera move, action, lighting change).  
- Keep identity consistent between the two stills when possible.

## R2V — Reference to video

- Load up to **five** reference images (and optional audio if your graph supports it).  
- Prompts are more “programmatic”: shots, timing, which picture is used when.  
- See **Prompting samples** for a starter template, and MiniMax’s official ref guide when you need depth.

## Tip

Change the Global Selector once, queue again. The Image Loaders, Prompt Engineer, MiniMax node, and Model Switcher should all follow that string.
