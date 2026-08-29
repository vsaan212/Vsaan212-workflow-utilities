"""Lazy Docs — index Markdown files under Docs/ and serve content for the viewer UI."""
from __future__ import annotations

import os
from typing import Any

try:
    import markdown as _markdown

    def _md_to_html(text: str) -> str:
        return _markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br"],
        )
except Exception:
    def _md_to_html(text: str) -> str:
        # Minimal fallback if the markdown package is missing.
        import html as _html

        escaped = _html.escape(text or "")
        return f"<pre style='white-space:pre-wrap;margin:0'>{escaped}</pre>"


DOCS_ROOT = os.path.join(os.path.dirname(__file__), "Docs")


def ensure_docs_root() -> str:
    os.makedirs(DOCS_ROOT, exist_ok=True)
    return DOCS_ROOT


def _normalize_subfolder(folder: str | None) -> str:
    raw = (folder or "").strip().replace("\\", "/").strip("/")
    if not raw:
        return ""
    parts = [p for p in raw.split("/") if p and p != "."]
    if any(p == ".." for p in parts):
        raise ValueError("invalid folder path")
    return "/".join(parts)


def resolve_under_docs(rel: str) -> str:
    """Resolve a relative path under Docs/; raise ValueError on escape."""
    ensure_docs_root()
    rel_norm = (rel or "").strip().replace("\\", "/").lstrip("/")
    parts = [p for p in rel_norm.split("/") if p and p != "."]
    if any(p == ".." for p in parts):
        raise ValueError("path escapes Docs root")
    full = os.path.normpath(os.path.join(DOCS_ROOT, *parts)) if parts else os.path.normpath(DOCS_ROOT)
    root = os.path.normpath(DOCS_ROOT)
    if full != root and not full.startswith(root + os.sep):
        raise ValueError("path escapes Docs root")
    return full


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse simple YAML-ish --- frontmatter; return (meta, body)."""
    raw = text or ""
    if not raw.startswith("---"):
        return {}, raw
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, raw
    meta: dict[str, Any] = {}
    i = 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            body = "\n".join(lines[i + 1 :])
            if body.startswith("\n"):
                body = body[1:]
            return meta, body
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                meta[key] = val
        i += 1
    return {}, raw


def _meta_index(meta: dict[str, Any]) -> int:
    try:
        return int(str(meta.get("index", "9999")).strip())
    except (TypeError, ValueError):
        return 9999


def list_subfolders() -> list[str]:
    ensure_docs_root()
    names: list[str] = []
    for name in os.listdir(DOCS_ROOT):
        path = os.path.join(DOCS_ROOT, name)
        if os.path.isdir(path) and not name.startswith("."):
            names.append(name.replace("\\", "/"))
    return sorted(names, key=lambda s: s.lower())


ROOT_LABEL = "(root)"


def folder_choices() -> list[str]:
    """Combo values: root label plus immediate subfolders of Docs/."""
    ensure_docs_root()
    return [ROOT_LABEL] + list_subfolders()


def normalize_folder_choice(folder: str | None) -> str:
    """Map widget value to API/subfolder path (empty string = root)."""
    raw = (folder or "").strip()
    if not raw or raw == ROOT_LABEL:
        return ""
    return _normalize_subfolder(raw)


def build_index(folder: str | None = "") -> list[dict[str, Any]]:
    """List .md files in Docs/ or Docs/<folder>/ (non-recursive)."""
    sub = _normalize_subfolder(folder)
    target = resolve_under_docs(sub)
    if not os.path.isdir(target):
        raise FileNotFoundError(f"folder not found: {sub or '(root)'}")

    entries: list[dict[str, Any]] = []
    for name in os.listdir(target):
        if not name.lower().endswith(".md"):
            continue
        if name.startswith("."):
            continue
        full = os.path.join(target, name)
        if not os.path.isfile(full):
            continue
        rel = name if not sub else f"{sub}/{name}"
        rel = rel.replace("\\", "/")
        try:
            with open(full, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        meta, _body = parse_frontmatter(text)
        stem = os.path.splitext(name)[0]
        title = str(meta.get("title") or "").strip() or stem
        entries.append(
            {
                "id": rel,
                "title": title,
                "index": _meta_index(meta),
                "path": rel,
            }
        )
    entries.sort(key=lambda e: (e["index"], e["title"].lower(), e["path"].lower()))
    return entries


def read_content(rel_path: str) -> dict[str, Any]:
    rel = (rel_path or "").strip().replace("\\", "/")
    if not rel.lower().endswith(".md"):
        raise ValueError("only .md files are allowed")
    full = resolve_under_docs(rel)
    if not os.path.isfile(full):
        raise FileNotFoundError(f"file not found: {rel}")
    with open(full, "r", encoding="utf-8") as f:
        text = f.read()
    meta, body = parse_frontmatter(text)
    stem = os.path.splitext(os.path.basename(full))[0]
    title = str(meta.get("title") or "").strip() or stem
    html = _md_to_html(body)
    return {
        "title": title,
        "path": rel,
        "index": _meta_index(meta),
        "raw": body,
        "html": html,
    }


def api_folders() -> dict[str, Any]:
    return {"folders": list_subfolders(), "root": "Docs"}


def api_index(folder: str | None = "") -> dict[str, Any]:
    try:
        sub = normalize_folder_choice(folder)
    except ValueError as e:
        return {"error": str(e), "folder": folder or "", "entries": []}
    try:
        entries = build_index(sub)
    except FileNotFoundError as e:
        return {"error": str(e), "folder": sub, "entries": []}
    except ValueError as e:
        return {"error": str(e), "folder": sub, "entries": []}
    return {"folder": sub, "entries": entries}


def api_content(path: str | None = "") -> dict[str, Any]:
    try:
        return read_content(path or "")
    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}


class LazyDocs:
    """Display-only Markdown documentation viewer (UI driven by js/lazy_docs.js)."""

    @classmethod
    def INPUT_TYPES(cls):
        choices = folder_choices()
        return {
            "required": {
                "docs_subfolder": (
                    choices,
                    {
                        "default": ROOT_LABEL,
                        "tooltip": (
                            "Doc set under lazy_docs/Docs/. "
                            f"{ROOT_LABEL} = Markdown files in Docs/ root. "
                            "Pick a subfolder (e.g. minimax_h3) to load only that set. "
                            "Press R or Refresh after adding folders."
                        ),
                    },
                ),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "noop"
    OUTPUT_NODE = True
    CATEGORY = "vsaan212/utilities"

    def noop(self, docs_subfolder: str = ROOT_LABEL):
        from ..lazy_logging import debug
        ensure_docs_root()
        _ = normalize_folder_choice(docs_subfolder)
        debug("Lazy Docs", f"viewer folder {docs_subfolder}")
        return {"ui": {}}


NODE_CLASS_MAPPINGS = {
    "LazyDocs": LazyDocs,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LazyDocs": "Lazy Docs",
}
