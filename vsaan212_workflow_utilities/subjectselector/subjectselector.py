import os
from typing import List


class ComfyUI_subjectselector:
    """
    Subject selector with recursive subfolder support.

    Place .txt files anywhere under:
      <this_repo>/SubjectFiles/

    Examples:
      SubjectFiles/
        alice.txt
        characters/
          main/
            ashley_summer.txt
          extras/
            vendor1.txt

    The dropdown shows relative paths WITHOUT the .txt extension:
      - "alice"
      - "characters/main/ashley_summer"
      - "characters/extras/vendor1"
    """
    subjects_relpaths: List[str] = []   # e.g., ["alice", "characters/main/ashley_summer"]
    root_dir: str = ""                  # absolute path to SubjectFiles

    @classmethod
    def INPUT_TYPES(cls):
        cls.refresh_subjects_list()
        subject_choices = sorted(cls.subjects_relpaths, key=lambda s: s.lower())
        return {
            "required": {
                "subject": (subject_choices,),
            },
            "optional": {
                "refresh": (["⟳ Refresh Subjects"],),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("text", "preview",)
    FUNCTION = "load_subject"
    CATEGORY = "vsaan212/Selectors"

    # ---------- Directory scanning ----------

    @classmethod
    def refresh_subjects_list(cls):
        """
        Walk SubjectFiles recursively, caching relative POSIX paths WITHOUT .txt
        for all subject files.
        """
        subject_dir = os.path.join(os.path.dirname(__file__), "SubjectFiles")
        cls.root_dir = subject_dir

        if not os.path.exists(subject_dir):
            os.makedirs(subject_dir, exist_ok=True)

        subjects: List[str] = []
        for root, _, files in os.walk(subject_dir):
            for f in files:
                if f.lower().endswith(".txt"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, subject_dir).replace("\\", "/")
                    subjects.append(rel_path[:-4])  # strip ".txt"

        cls.subjects_relpaths = subjects

    # ---------- Node function ----------

    def load_subject(self, subject, refresh=None):
        """
        Load the selected subject (relative path without .txt).
        Returns: (file text, preview string).
        """
        rel_no_ext = (subject or "").strip().replace("\\", "/").strip("/")
        if not rel_no_ext:
            return ("", "No subject selected.")

        file_path = os.path.join(self.root_dir, f"{rel_no_ext}.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip().replace("\r\n", "\n").replace("\r", "\n")
            preview = f"Loaded: {rel_no_ext}.txt"
        except Exception as e:
            content = f"Error loading subject file: {e}"
            preview = f"Failed to load: {rel_no_ext}.txt"

        return (content, preview)


# ✅ Required: register the node with ComfyUI
NODE_CLASS_MAPPINGS = {
    "ComfyUI_subjectselector": ComfyUI_subjectselector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI_subjectselector": "Subject Selector"
}
