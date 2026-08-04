# Lazy MiniMax (H3)

Local MiniMax H3 helpers for this pack. Conditioning logic is based on ComfyUI core nodes in:

- Upstream: [`comfy_extras/nodes_minimax_h3.py`](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_minimax_h3.py)
- Nodes: `MiniMaxH3ImageToVideo`, `MiniMaxH3ReferenceToVideo` (and related AV latent / sigma helpers)

**Thanks to [Comfy-Org / ComfyUI](https://github.com/Comfy-Org/ComfyUI)** for the native H3 integration (PR [#15224](https://github.com/Comfy-Org/ComfyUI/pull/15224)).

Requires ComfyUI **0.30.0+** with native MiniMax H3 support. The all-in-one node delegates to those core classes when available.

> Note: the older MiniMax **cloud API** file (`comfy_api_nodes/nodes_minimax.py`) is not part of this pack.
