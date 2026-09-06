from .lazy_subject_scene_automation import (
    NODE_CLASS_MAPPINGS as _SAS_CLASSES,
    NODE_DISPLAY_NAME_MAPPINGS as _SAS_DISPLAY,
    LazySubjectSceneAutomation,
)
from .lazy_refmod_split import (
    NODE_CLASS_MAPPINGS as _SPLIT_CLASSES,
    NODE_DISPLAY_NAME_MAPPINGS as _SPLIT_DISPLAY,
    LazyRefmodSplit,
)

NODE_CLASS_MAPPINGS = {**_SAS_CLASSES, **_SPLIT_CLASSES}
NODE_DISPLAY_NAME_MAPPINGS = {**_SAS_DISPLAY, **_SPLIT_DISPLAY}

__all__ = [
    "LazySubjectSceneAutomation",
    "LazyRefmodSplit",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
