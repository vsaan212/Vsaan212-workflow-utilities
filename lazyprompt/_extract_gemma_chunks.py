"""One-off helper — run from repo root to refresh presets from Gemma4Prompt copy."""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent
_SRC = _ROOT / "Gemma4Prompt" / "gemma4_prompt_gen.py"


def main():
    lines = _SRC.read_text(encoding="utf-8").splitlines()
    env = (
        '"""Environment presets for LazyPrompt (location, lighting, sound). '
        'Ported from Gemma4Prompt."""\n\n'
        + "\n".join(lines[45:916])
        + "\n"
    )
    (_HERE / "environment_presets.py").write_text(env, encoding="utf-8")
    sys_h = (
        '"""Target-model system prompts and router (LazyPrompt). '
        'Ported from Gemma4Prompt."""\n\n'
        + "\n".join(lines[921:1248])
        + "\n"
    )
    (_HERE / "system_prompts.py").write_text(sys_h, encoding="utf-8")
    print("OK", len(lines[45:916]), len(lines[921:1248]))


if __name__ == "__main__":
    main()
