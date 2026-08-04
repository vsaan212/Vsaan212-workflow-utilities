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
    # System prompts now live in lazyprompt/Model_Skills/*.md (editable defaults).
    print("OK", len(lines[45:916]), "(environment_presets only; edit Model_Skills/*.md for templates)")


if __name__ == "__main__":
    main()
