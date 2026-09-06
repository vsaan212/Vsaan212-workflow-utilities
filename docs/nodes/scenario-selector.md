# Scenario Selector

**ComfyUI node:** `ComfyUI_ScenarioSelector` · **Menu:** `vsaan212/Selectors`

## What it does

Loads the full text of a `.txt` file from **`ComfyUI/lazynodes/scenarioselector/ScenarioFiles/`** (recursive subfolders). Use it for episode beats, location packs, or any reusable scenario text.

## Workflow usage

1. Put `.txt` files under `ComfyUI/lazynodes/scenarioselector/ScenarioFiles/`. On first startup the pack creates that folder and copies shipped examples if they are missing.
2. Add **Scenario Selector** to the graph.
3. Refresh the dropdown with ComfyUI **`R`** or by recreating the node if new files do not appear.
4. Wire **`text`** into downstream nodes (prompt builders, previews, your own parsers).
5. **`preview`** shows a short load status.

## Dropdown paths

Relative path **without** the `.txt` extension, e.g. `sets/city/night_market` → `ScenarioFiles/sets/city/night_market.txt`.

## API note

`GET /vsaan212/scenarios` serves the file list for the refresh extension.

## See also

- [Subject Selector](subject-selector.md)
- [Lazy-subject-and-scene-automation](lazy-subject-scene-automation.md) — uses its own `ScenarioFiles` under `ComfyUI/lazynodes/lazy_subject_scene_automation/`.
