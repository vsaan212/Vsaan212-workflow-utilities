---
title: Using Lazy Docs
index: 0
---

# Using Lazy Docs

Drop `.md` files into this pack’s **`lazy_docs/Docs/`** folder.

## Frontmatter

```md
---
title: My page title
index: 10
---

Body markdown…
```

- **`title`** — label in the left index (defaults to the filename).
- **`index`** — sort order (lower first). Missing → `9999`.

## Subfolders

- Leave **Folder** empty to list `.md` files in `Docs/` root only.
- Set **Folder** to a subfolder name (e.g. `minimax_h3`) to list only that folder’s files.
- Same value is editable from the node field, **Refresh**, or right-click → **Set Docs subfolder…** / Properties (`docs_subfolder`).

## Viewing

Click an index link to load the page on the right. Toggle **Raw** for source Markdown.
