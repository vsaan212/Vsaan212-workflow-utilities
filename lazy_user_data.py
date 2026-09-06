"""
Persistent user libraries for this pack.

ComfyUI Manager / zip updates replace ``custom_nodes/<this pack>/`` and would
wipe subject files, scenario files, and ``lazy_prompts.json`` if they lived
inside the pack. Those libraries are stored under:

    <ComfyUI>/lazynodes/

On first load (and after each ComfyUI restart) missing files are copied from
the pack's shipped defaults. Existing user files are never overwritten.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
from typing import Optional

from .lazy_logging import debug

LAZYNODES_DIRNAME = "lazynodes"

_SKIP_DIR_NAMES = {".git", "__pycache__", ".ds_store"}

# (relative dest under lazynodes, relative source under this pack)
_TREE_MAP = (
    (
        os.path.join("lazy_subject_scene_automation", "SubjectFiles"),
        os.path.join("lazy_subject_scene_automation", "SubjectFiles"),
    ),
    (
        os.path.join("lazy_subject_scene_automation", "ScenarioFiles"),
        os.path.join("lazy_subject_scene_automation", "ScenarioFiles"),
    ),
    (
        os.path.join("subjectselector", "SubjectFiles"),
        os.path.join("subjectselector", "SubjectFiles"),
    ),
    (
        os.path.join("scenarioselector", "ScenarioFiles"),
        os.path.join("scenarioselector", "ScenarioFiles"),
    ),
)

_PROMPTS_DEST = "lazy_prompts.json"
_PROMPTS_PACK = os.path.join("lazy_prompt_saver", "lazy_prompts.json")

_README_NAME = "README.txt"
_README_BODY = (
    "Vsaan212 Workflow Utilities — user libraries\n"
    "\n"
    "This folder is outside custom_nodes so Manager / zip updates of the pack\n"
    "do not delete your files.\n"
    "\n"
    "  lazy_subject_scene_automation/SubjectFiles/\n"
    "  lazy_subject_scene_automation/ScenarioFiles/\n"
    "  subjectselector/SubjectFiles/\n"
    "  scenarioselector/ScenarioFiles/\n"
    "  lazy_prompts.json\n"
    "\n"
    "Shipped example .txt files are copied here only if missing. Your own files\n"
    "are never overwritten. After adding files, press R in ComfyUI to refresh\n"
    "dropdowns.\n"
)

_lock = threading.Lock()
_seeded = False


def pack_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def comfy_base_path() -> str:
    """ComfyUI install root (same folder as custom_nodes, input, output)."""
    try:
        import folder_paths

        base = getattr(folder_paths, "base_path", None) or ""
        if base and os.path.isdir(str(base)):
            return os.path.abspath(str(base))
    except Exception:
        pass
    return os.path.abspath(os.path.join(pack_root(), "..", ".."))


def lazynodes_root() -> str:
    return os.path.join(comfy_base_path(), LAZYNODES_DIRNAME)


def _copy_missing_tree(src: str, dest: str) -> int:
    """Copy files from src to dest when the dest file does not exist."""
    os.makedirs(dest, exist_ok=True)
    if not src or not os.path.isdir(src):
        return 0
    src_abs = os.path.abspath(src)
    dest_abs = os.path.abspath(dest)
    if src_abs == dest_abs:
        return 0
    copied = 0
    for root, dirs, files in os.walk(src_abs):
        dirs[:] = [d for d in dirs if d.lower() not in _SKIP_DIR_NAMES]
        rel_root = os.path.relpath(root, src_abs)
        dest_root = dest_abs if rel_root == "." else os.path.join(dest_abs, rel_root)
        os.makedirs(dest_root, exist_ok=True)
        for fname in files:
            if fname.endswith((".pyc", ".pyo")):
                continue
            src_file = os.path.join(root, fname)
            dest_file = os.path.join(dest_root, fname)
            if os.path.isfile(dest_file):
                continue
            try:
                shutil.copy2(src_file, dest_file)
                copied += 1
            except OSError as e:
                debug("lazy_user_data", f'copy failed "{src_file}" → "{dest_file}": {e}')
    return copied


def _copy_missing_file(src: str, dest: str) -> bool:
    if os.path.isfile(dest):
        return False
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    if src and os.path.isfile(src):
        try:
            shutil.copy2(src, dest)
            return True
        except OSError as e:
            debug("lazy_user_data", f'copy failed "{src}" → "{dest}": {e}')
            return False
    if dest.endswith(".json"):
        try:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return True
        except OSError as e:
            debug("lazy_user_data", f'could not create "{dest}": {e}')
    return False


def _seed_all(root: str) -> None:
    pack = pack_root()
    os.makedirs(root, exist_ok=True)
    readme = os.path.join(root, _README_NAME)
    if not os.path.isfile(readme):
        try:
            with open(readme, "w", encoding="utf-8", newline="\n") as f:
                f.write(_README_BODY)
        except OSError as e:
            debug("lazy_user_data", f"could not write README: {e}")

    total = 0
    for rel_dest, rel_src in _TREE_MAP:
        dest = os.path.join(root, rel_dest)
        src = os.path.join(pack, rel_src)
        total += _copy_missing_tree(src, dest)

    dest_prompts = os.path.join(root, _PROMPTS_DEST)
    src_prompts = os.path.join(pack, _PROMPTS_PACK)
    if _copy_missing_file(src_prompts, dest_prompts):
        total += 1

    debug(
        "lazy_user_data",
        f'seeded "{root}" ({total} new file(s) from pack defaults / leftover pack copies)',
    )


def ensure_seeded() -> str:
    """
    Create <ComfyUI>/lazynodes if needed and copy missing shipped defaults.
    Safe to call often; seeding runs once per process.
    """
    global _seeded
    with _lock:
        root = lazynodes_root()
        try:
            os.makedirs(root, exist_ok=True)
            if not _seeded:
                _seed_all(root)
                _seeded = True
        except OSError as e:
            debug("lazy_user_data", f'could not use lazynodes at "{root}": {e}')
            return pack_root()
        return root


def _dir_under_lazynodes(*parts: str, pack_fallback: Optional[str] = None) -> str:
    root = ensure_seeded()
    path = os.path.join(root, *parts)
    if os.path.isdir(path) or root != pack_root():
        os.makedirs(path, exist_ok=True)
        return path
    fallback = pack_fallback or os.path.join(pack_root(), *parts)
    os.makedirs(fallback, exist_ok=True)
    return fallback


def sas_subject_files() -> str:
    return _dir_under_lazynodes("lazy_subject_scene_automation", "SubjectFiles")


def sas_scenario_files() -> str:
    return _dir_under_lazynodes("lazy_subject_scene_automation", "ScenarioFiles")


def selector_subject_files() -> str:
    return _dir_under_lazynodes("subjectselector", "SubjectFiles")


def selector_scenario_files() -> str:
    return _dir_under_lazynodes("scenarioselector", "ScenarioFiles")


def lazy_prompts_path() -> str:
    root = ensure_seeded()
    path = os.path.join(root, _PROMPTS_DEST)
    if not os.path.isfile(path):
        _copy_missing_file(os.path.join(pack_root(), _PROMPTS_PACK), path)
    if os.path.isfile(path):
        return path
    fallback = os.path.join(pack_root(), _PROMPTS_PACK)
    os.makedirs(os.path.dirname(fallback), exist_ok=True)
    return fallback
