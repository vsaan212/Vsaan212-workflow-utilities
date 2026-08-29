import re
import sys
from typing import List, Tuple

from ..lazy_logging import debug

# Version compatibility check
MIN_PYTHON_VERSION = (3, 7)
if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher is required")


def _split_tagged_sections(content: str, trim_whitespace: bool = True) -> List[str]:
    """
    Split subject/scenario-style tagged files: [Tag] header lines (optional
    [strength] groups on the same line) followed by body until the next tag.
    Returns section bodies in file order; tag names are not included in output.
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    sections: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if not stripped.startswith("["):
            i += 1
            continue
        if not re.findall(r"\[([^\]]*)\]", stripped):
            i += 1
            continue

        i += 1
        body_lines: List[str] = []
        while i < n:
            nxt = lines[i]
            if nxt.strip().startswith("["):
                break
            body_lines.append(nxt)
            i += 1
        body = "\n".join(body_lines)
        if trim_whitespace:
            body = body.strip()
        sections.append(body)

    return sections


def _first_line_is_lorahigha(content: str) -> bool:
    """True when the first non-empty line opens a v2 subject/scenario file ([LoraHighA]…)."""
    for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("["):
            return False
        groups = re.findall(r"\[([^\]]*)\]", stripped)
        if not groups:
            return False
        tag = re.sub(r"[^a-z0-9]", "", groups[0].lower())
        return tag == "lorahigha"
    return False


class TextSplitNode:
    """
    Custom ComfyUI node to split text into multiple outputs for feeding complex multi-scene renders.
    Supports custom separators and dynamic output count with remainder output.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "separator": ("STRING", {"default": "|"}),
                "num_splits": ("INT", {"default": 2, "min": 1, "max": 8}),
                "trim_whitespace": ("BOOLEAN", {"default": True}),
                "remove_empty": ("BOOLEAN", {"default": True}),
                "tagged_format": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": (
                            "Split at [Tag] lines. Auto-enabled when the first non-empty line "
                            "is [LoraHighA] (v2 subject/scenario files). Otherwise this toggle applies."
                        ),
                    },
                ),
            }
        }
    
    FUNCTION = "split_text"
    CATEGORY = "vsaan212/utilities"


    # For dynamic outputs, we need to handle this differently
    # The node will always show the maximum number of outputs
    # but only the first num_splits + 1 will contain data
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text_1", "text_2", "text_3", "text_4", "text_5", "text_6", "text_7", "text_8", "remainder")
    
    def split_text(
        self,
        text: str,
        separator: str = "|",
        num_splits: int = 2,
        trim_whitespace: bool = True,
        remove_empty: bool = True,
        tagged_format: bool = False,
    ) -> Tuple[str, ...]:
        """
        Split the input text into multiple outputs based on the separator.
        
        Args:
            text: Input text to split
            separator: Custom separator string or regex pattern
            num_splits: Number of splits to create (1-8)
            trim_whitespace: Whether to trim whitespace from split parts
            remove_empty: Whether to remove empty parts
            
        Returns:
            Tuple with split text outputs and remainder (always 9 outputs total)
        """
        if not text:
            # Return empty strings for all 9 outputs (8 splits + remainder)
            return tuple([""] * 9)

        use_tagged = _first_line_is_lorahigha(text) or tagged_format
        debug(
            "Text Split",
            f"{'tagged' if use_tagged else 'separator'} split num_splits={num_splits}",
        )

        if use_tagged:
            parts = _split_tagged_sections(text, trim_whitespace=trim_whitespace)
        elif separator.startswith('/') and separator.endswith('/'):
            pattern = separator[1:-1]  # Remove the / / delimiters
            pattern = pattern.replace('\\\\', '\\')
            parts = re.split(pattern, text)
        else:
            parts = text.split(separator)
        
        # Process parts
        processed_parts = []
        for part in parts:
            if not use_tagged and trim_whitespace:
                part = part.strip()
            if not remove_empty or part:
                processed_parts.append(part)
        
        # Split into main parts and remainder
        main_parts = processed_parts[:num_splits]
        remainder_parts = processed_parts[num_splits:]
        
        # Pad main parts to exactly 8 outputs
        while len(main_parts) < 8:
            main_parts.append("")
        
        # Join remainder parts
        remainder = separator.join(remainder_parts) if remainder_parts else ""
        
        # Return tuple: 8 main parts + remainder (9 total)
        return tuple(main_parts + [remainder])
    

