import os
from typing import List


class ComfyUI_ScenarioSelector:
    """
    Scenario selector with recursive subfolder support.

    Put .txt files anywhere under:
      <this_repo>/ScenarioFiles/

    Examples:
      ScenarioFiles/
        my_scene.txt
        sets/
          city/
            night_market.txt
          nature/
            forest_walk.txt

    The dropdown shows relative paths WITHOUT the .txt extension:
      - "my_scene"
      - "sets/city/night_market"
      - "sets/nature/forest_walk"
    """
    scenarios_relpaths: List[str] = []   # e.g., ["my_scene", "sets/city/night_market"]
    root_dir: str = ""                   # absolute path to ScenarioFiles

    @classmethod
    def INPUT_TYPES(cls):
        cls.refresh_scenarios_list()
        scenario_choices = sorted(cls.scenarios_relpaths, key=lambda s: s.lower())
        return {
            "required": {
                "scenario": (scenario_choices,),
            },
            "optional": {
                "refresh": (["⟳ Refresh Scenarios"],),
            },
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("text", "preview",)
    FUNCTION = "load_scenario"
    CATEGORY = "vsaan212/Selectors"

    # ---------- Directory scanning ----------

    @classmethod
    def refresh_scenarios_list(cls):
        """
        Walk ScenarioFiles recursively, caching:
          - scenarios_relpaths: relative POSIX paths WITHOUT .txt
        """
        scenario_dir = os.path.join(os.path.dirname(__file__), "ScenarioFiles")
        cls.root_dir = scenario_dir

        if not os.path.exists(scenario_dir):
            os.makedirs(scenario_dir, exist_ok=True)

        scenarios: List[str] = []
        for root, _, files in os.walk(scenario_dir):
            for f in files:
                if f.lower().endswith(".txt"):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, scenario_dir).replace("\\", "/")
                    scenarios.append(rel_path[:-4])  # strip ".txt"

        cls.scenarios_relpaths = scenarios

    # ---------- Node function ----------

    def load_scenario(self, scenario, refresh=None):
        """
        Load the selected scenario (relative path without .txt).
        Returns: (file text, preview string).
        """
        rel_no_ext = (scenario or "").strip().replace("\\", "/").strip("/")
        if not rel_no_ext:
            return ("", "No scenario selected.")

        file_path = os.path.join(self.root_dir, f"{rel_no_ext}.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip().replace("\r\n", "\n").replace("\r", "\n")
            preview = f"Loaded: {rel_no_ext}.txt"
        except Exception as e:
            content = f"Error loading scenario file: {e}"
            preview = f"Failed to load: {rel_no_ext}.txt"

        return (content, preview)


# Register node with ComfyUI
NODE_CLASS_MAPPINGS = {
    "ComfyUI_ScenarioSelector": ComfyUI_ScenarioSelector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI_ScenarioSelector": "Scenario Selector"
}
