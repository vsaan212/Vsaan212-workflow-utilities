# Lazy Prompt Saver

**ComfyUI node:** `LazyPromptSaver` · **Menu:** `vsaan212/utilities`

## What it does

Stores reusable prompt snippets in a local **`lazy_prompts.json`** file next to the node code. You can name prompts, edit text in the graph, save, clone, and delete without leaving ComfyUI.

## Workflow usage

1. Add **Lazy Prompt Saver** where you want a persistent prompt source.
2. Type a **`prompt_name`** and **`prompt_text`** (multiline supported).
3. Choose an existing entry from **`saved_prompts`** to load it into the widgets.
4. **Save** — writes the current name + text to `lazy_prompts.json`.
5. **Clone** — duplicates the current name with a `_copy` suffix for editing (does not persist until you **Save**).
6. **Delete** — removes the selected entry after confirmation.
7. Connect the **`prompt_text`** output to **CLIP Text Encode**, conditioning inputs, or downstream string nodes.

## Tips

- The dropdown updates after each save/delete.
- Use consistent naming (e.g. `portrait_neutral`, `scene_night_city`) so subgraphs stay readable.
- Back up `lazy_prompts.json` if you rely on it across ComfyUI updates or machine moves.

## See also

[LazyPrompt](lazyprompt.md) — LLM-expanded prompts rather than static library snippets.
