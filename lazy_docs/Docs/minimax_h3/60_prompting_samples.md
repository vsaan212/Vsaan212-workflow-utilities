---
title: Prompting samples
index: 60
---

# Prompting samples (copy and adapt)

These are **short user ideas** you can paste into Prompt Engineer **`user_input`** (with the matching **`target_model`**). The LLM expands them into full MiniMax structure when bypass is OFF.

Also keep **`video_length`** close to your real clip length.

---

## I2V — start from one image

**User idea (short):**

```text
She turns toward the camera, soft smile, hair moves in a light breeze. Slow push-in. Soft outdoor ambience, distant birds.
```

**What to remember**

- Do **not** re-describe the whole photo. Assume the first frame is already correct.  
- Describe **motion**, camera, and sound.  
- If you wired the first frame into LM Studio vision, the model can lock clothing/face from the image.

**Subject file `[desciption]` example:**

```text
Young woman, short black hair, green jacket, calm neutral expression
```

---

## FL2V — first frame → last frame

**User idea:**

```text
Start on a quiet street at dusk. She walks toward the doorway. End on a close-up of her hand on the doorknob. Camera tracks beside her at walking pace. City hum, footsteps.
```

Keep start and end stills consistent (same person, outfit, lighting family).

---

## T2V — text only

**User idea:**

```text
Live-action cinematic wide shot of a rainy neon alley. A courier on a bike cuts through puddles. Camera trucks left at medium speed. Rain on metal, distant traffic, soft synth bed.
```

No images required. Be specific about shot size, camera move, action, and sound.

---

## R2V — reference style (starter)

R2V prompts are more structured. Official deep guide:

https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md

**Short user idea to expand:**

```text
Use Picture 1 as the hero identity. Shot 1: medium shot, she looks left then walks forward. At 00:03 cut to Shot 2 closer on her hands adjusting a scarf. Soft room tone, no music.
```

Say which reference picture anchors identity, and keep shot times increasing inside the clip.

---

## Using a scenario `[Prompt]` block instead

If your **scenario** `.txt` contains:

```text
[Prompt]
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, medium shot...
overall_soundscape: soft wind, distant city
non_diegetic_music: none
```

Wire automation **`prompt_override`** → Prompt Engineer **`prompt_override_input`**. That text becomes the main idea sent to the LLM (or the full prompt if you turn **bypass** ON).

---

## Random spice in scene files

In scenario text you can write choices like:

```text
She wears a {red|blue|black} coat
```

The automation node picks one option each queue.

---

## Dialogue tip

Only add spoken lines if you actually want dialogue. Give stable speaker tags in the long form (the skill templates use patterns like `(S1)`). Keep quotes in your short user idea if you need exact wording preserved.
