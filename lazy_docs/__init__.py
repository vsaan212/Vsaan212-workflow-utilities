from .lazy_docs import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    LazyDocs,
    ROOT_LABEL,
    api_content,
    api_folders,
    api_index,
    ensure_docs_root,
    folder_choices,
    normalize_folder_choice,
)

ensure_docs_root()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "LazyDocs",
    "ROOT_LABEL",
    "api_content",
    "api_folders",
    "api_index",
    "ensure_docs_root",
    "folder_choices",
    "normalize_folder_choice",
]
