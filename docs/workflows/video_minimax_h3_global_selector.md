# MiniMax H3 — global selector workflow

**Template:** [video_minimax_h3_global_selector.json](video_minimax_h3_global_selector.json)

Streamlined MiniMax H3 graph: one **Lazy Global Selector** drives Image Loader hard-gates, Prompt Engineer media sockets, subject/scene `[Workflow]`, MiniMax conditioner mode, and UNET routing via **Lazy Model Switcher**.

## Modes

| Mode | Images | UNET |
|------|--------|------|
| `T2V` | none | fl2va |
| `I2V` | first frame | fl2va |
| `FL2V` | first + last | fl2va |
| `R2V` | refs 1–5 + audio | ref2va |

## Operator flow

1. Set **Lazy Global Selector** to the mode you want.
2. Load images on the role-matched Image Loaders (others emit nothing).
3. Optional: use SAS subject/scenario files with `[Workflow]` / `[ReferenceImage1]`…`5` / `[AudioReference]` — SAS overrides direct image sockets on Prompt Engineer when its selector blob is wired.
4. Queue once — Model Switcher picks the matching UNET; MiniMax ignores unused media.

No need to mute branches or swap Set/Get paths between modes.
