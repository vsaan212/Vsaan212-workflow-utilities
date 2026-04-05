# Text Split

**ComfyUI node:** `Vsaan_TextSplit` · **Menu:** `vsaan212/utilities` · **Display name:** Text Split (by separator)

## What it does

Splits one multiline `STRING` into up to **eight** segments plus a **remainder**, using a separator you choose. Useful when a single prompt text must drive several CLIP encoders, KSamplers, or schedule slots.

## Inputs (workflow tips)

| Input | Usage |
|--------|--------|
| `text` | Full string to split (often from a selector or upstream prompt node). |
| `separator` | String split, **or** a regex wrapped in `/.../` (e.g. `/\\|/` for alternation). |
| `num_splits` | How many primary outputs (`text_1` … `text_n`) to fill before the remainder. |
| `trim_whitespace` | Trim each chunk (usually leave on). |
| `remove_empty` | Drop empty pieces so indices stay meaningful. |

## Outputs

Always **nine** sockets: `text_1` … `text_8`, then `remainder`. Only the first `num_splits` chunks plus `remainder` are meaningful; unused `text_*` slots are empty strings.

## Workflow patterns

- **Parallel encoders:** Connect `text_1`, `text_2`, … to separate CLIP Text Encode nodes for multi-part prompts.
- **Regex:** Use `/pattern/` when the delimiter is not a fixed string.
- **Remainder:** Use `remainder` for “everything after the Nth split” without losing material.

## See also

Nodes that output a single combined string (selectors, Lazy Prompt Saver, LazyPrompt) often feed this node’s `text` input.
