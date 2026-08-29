---
title: Troubleshooting
index: 80
---

# Troubleshooting

## Lazy Multi Frame Select grid is empty / prompt stuck executing

- Restart ComfyUI after updating the pack so `js/lazy_multi_frame_select.js` loads.  
- Click **Continue** on that node. Do **not** queue a second prompt to confirm the pick.  
- **Cancel** on the node (or ComfyUI stop) ends the wait. **Clear** only deselects frames.

## SamplerCustomAdvanced / float division by zero (T2V only)

MiniMax builds a spatial layout from latent **width × height**. In T2V the first-frame loader correctly emits no image and **`0×0`** size. If Auto width/height still takes “from first frame” for every non-R2V mode, the empty latent is `0×0` and sampling crashes inside `PackedLayout`.

**Fix:** On the Lazy Switch (Integer) nodes that feed Auto width / Auto height, set **`match`** to `t2v,r2v` so T2V and R2V use **ResolutionSelector**, while I2V / FL2V keep first-frame size. Reload custom nodes if the switch does not accept comma-separated match yet.

## Image did not affect the video

- Check Global Selector mode (I2V needs first frame; FL2V needs first+last; R2V needs refs).  
- Confirm the Image Loader **workflow_role** matches that mode.  
- Confirm `global_selector_input` is wired from the Global Selector.

## LLM errors / empty prompt

- LM Studio: is the server running? Does **lm_studio_model** match exactly?  
- Try **bypass** ON to confirm the rest of the graph works.  
- Lower **creativity** to ≤ 1.0.  
- Raise **max_output_tokens** if answers look cut off.

## Subject / scene LoRA did nothing

- Is the path real and discoverable by Comfy?  
- Is the slot set to **`bypass`**?  
- Are you editing the **live pane** but expecting the **disk** file? Queue uses the pane; use **Save edits** to write disk.  
- Press **R** after adding new `.txt` files.

## Wrong UNET / weird R2V behavior

- Model Switcher should receive the mode string (`selector` / `selector_Out`).  
- R2V needs the **ref2va** model on the ref input of the switcher.

## Docs node shows nothing in this guide

- Folder must be exactly: `local_minimax_h3`  
- Files must be under: `lazy_docs/Docs/local_minimax_h3/*.md`  
- Click **Refresh** on Lazy Docs  

## Still stuck

Check the ComfyUI console log for lines starting with `[LazyPrompt]`, MiniMax errors, or missing model paths. Fix the first red error — later nodes often fail only because an earlier one returned empty.
