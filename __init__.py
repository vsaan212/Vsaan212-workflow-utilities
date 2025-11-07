# __init__.py at repo root (pack root)
import os

# Ensure data folders exist (harmless if present)
_pkg_dir = os.path.dirname(__file__)
for _d in ("ScenarioFiles", "SubjectFiles"):
    os.makedirs(os.path.join(_pkg_dir, _d), exist_ok=True)

# Text Split
try:
    from .textsplit import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )
except Exception:
    from .textsplit.text_split_node import (
        NODE_CLASS_MAPPINGS as TS_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as TS_DISPLAY,
    )

# Optional Switch LoRA
try:
    from .optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )
except Exception:
    from .optional_switch_lora.optional_switch_lora import (
        NODE_CLASS_MAPPINGS as LORA_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY,
    )

# Scenario Selector
try:
    from .scenarioselector import (
        NODE_CLASS_MAPPINGS as SCEN_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
    )
except Exception:
    from .scenarioselector.scenarioselector import (
        NODE_CLASS_MAPPINGS as SCEN_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SCEN_DISPLAY,
    )

# Subject Selector
try:
    from .subjectselector import (
        NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
    )
except Exception:
    from .subjectselector.subjectselector import (
        NODE_CLASS_MAPPINGS as SUBJ_CLASSES,
        NODE_DISPLAY_NAME_MAPPINGS as SUBJ_DISPLAY,
    )

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
