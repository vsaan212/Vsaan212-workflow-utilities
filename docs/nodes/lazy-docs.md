# Lazy Docs

**ComfyUI node:** `LazyDocs` · **Menu:** `vsaan212/utilities` · **Display:** Lazy Docs

Display-only Markdown documentation viewer. Left pane = ordered index from frontmatter; click a title to load the page on the right (HTML by default, **Raw** toggle for source).

## Docs folder

Pack path: `lazy_docs/Docs/`

| Doc set (`docs_subfolder`) | Behavior |
|----------------------------|----------|
| **`(root)`** | Lists `.md` files in `Docs/` root only |
| **`minimax_h3`** | Lists `.md` files in `Docs/minimax_h3/` only (non-recursive) |

Pick the set from the **combo** on the node (and the matching **Doc set** dropdown in the viewer toolbar). Both stay in sync. **Refresh** reloads the folder list from disk and rebuilds the index. Right-click → **Refresh Lazy Docs sets** does the same.

After adding a new subfolder under `Docs/`, press **Refresh** (or Comfy **R** / reload) so it appears in the dropdown.
## Frontmatter

```md
---
title: Modes / how to use
index: 20
---

Body…
```

- **`title`** — index label (fallback: filename stem)
- **`index`** — sort key (missing → `9999`)

## UI

| Control | Action |
|---------|--------|
| **Doc set** dropdown | Pick `(root)` or a subfolder under `Docs/` |
| Index links | Load that file on the right |
| **Raw** | Show Markdown source instead of HTML |
| **Refresh** | Re-scan doc-set folders + reload the index |

Markdown is rendered **in the browser** from the file source (same idea as Comfy’s built-in **Markdown Note** under `utilities`). It does not require the Python `markdown` package in Comfy’s venv. Last selected path is stored in `docs_selected` so the pane restores after reopen.

## Shipped samples

- `Docs/readme.md` — how to use the Docs folder
- `Docs/minimax_h3/` — MiniMax H3 workflow notes (overview, modes, models, requirements, tips, prompting)

Point **Folder** at `minimax_h3` on graphs that previously used Note nodes for that pack.

## API

| Route | Purpose |
|-------|---------|
| `GET /vsaan212/lazy-docs/folders` | Subfolder names under `Docs/` |
| `GET /vsaan212/lazy-docs/index?folder=` | Sorted index entries |
| `GET /vsaan212/lazy-docs/content?path=` | `{title, raw, html}` |

Paths are constrained under `Docs/` (no `..` escape).

## Dependency

Optional: the Python **`markdown`** package can still fill the API `html` field. The Lazy Docs UI renders Markdown **client-side** and does not need it (same approach as Comfy **Markdown Note**).
