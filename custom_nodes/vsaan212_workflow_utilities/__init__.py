# custom_nodes/vsaan212_workflow_utilities/__init__.py
import os

# --- Ensure data folders exist on import (harmless if already present) ---
_pkg_dir = os.path.dirname(__file__)
for _d in ("ScenarioFiles", "SubjectFiles"):
    os.makedirs(os.path.join(_pkg_dir, _d), exist_ok=True)

# --- Robust imports for each submodule (handles legacy filenames too) ---
# Text Split
try:
    from .textsplit.text_split_node import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )
except Exception:
    # fallback for legacy single-file layout
    from .textsplit import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )

# Optional Switch LoRA (autobypass)
try:
    from .optional_switch_lora.optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )
except Exception:
    # fallback for legacy filename
    from .optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )

# Scenario Selector
try:
    from .scenarioselector.scenarioselector import (
        NODE_CLASS_MAPPINGS as SCEN_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
    )
except Exception:
    # fallback for legacy filename (senarioselector.py)
    try:
        from .scenarioselector.senarioselector import (
            NODE_CLASS_MAPPINGS as SCEN_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
        )
    except Exception:
        from .scenarioselector import (
            NODE_CLASS_MAPPINGS as SCEN_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
        )

# Subject Selector
try:
    from .subjectselector.subjectselector import (
        NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
    )
except Exception:
    # fallback for legacy filename (subjectselctor.py)
    try:
        from .subjectselector.subjectselctor import (
            NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
        )
    except Exception:
        from .subjectselector import (
            NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
            NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
        )

# --- Merge exports for ComfyUI ---
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

NODE_CLASS_MAPPINGS.update(TS_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(TS_DISPLAY)

NODE_CLASS_MAPPINGS.update(LORA_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(LORA_DISPLAY)

NODE_CLASS_MAPPINGS.update(SCEN_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(SCEN_DISPLAY)

NODE_CLASS_MAPPINGS.update(SUBJ_CLASSES)
NODE_DISPLAY_NAME_MAPPINGS.update(SUBJ_DISPLAY)
