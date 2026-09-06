# Subject Selector

**ComfyUI node:** `ComfyUI_subjectselector` · **Menu:** `vsaan212/Selectors`

## What it does

Loads the full text of a `.txt` file you pick from a dropdown. The list is built by scanning **`ComfyUI/lazynodes/subjectselector/SubjectFiles/`** recursively, so you can organize many character or subject definitions without hard-coding paths in the graph.

## Workflow usage

1. Place `.txt` files under `ComfyUI/lazynodes/subjectselector/SubjectFiles/` (any subfolders allowed). On first startup the pack creates that folder and copies shipped examples if they are missing.
2. Add **Subject Selector** to the graph.
3. Press **`R`** in ComfyUI (or recreate the node) if you added files and the dropdown looks stale — a small extension refreshes the list when the node is created.
4. Connect **`text`** to anything that needs the raw file contents (another node, a preview, a `String` input on a custom chain).
5. Use **`preview`** for a short status string (e.g. which file loaded).

## Dropdown paths

Entries are **relative paths without `.txt`**, POSIX-style, e.g. `characters/main/ashley_summer` for `SubjectFiles/characters/main/ashley_summer.txt`.

## API note

The pack exposes `GET /vsaan212/subjects` for the same list (used by the frontend refresh script).

## See also

- [Scenario Selector](scenario-selector.md) — same pattern for scene files.
- [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) — **different folder** under `lazynodes/lazy_subject_scene_automation/`; combines subject + scenario + LoRA stacks in one node.
