import re
import sys
from typing import List, Dict, Any, Tuple, Union

# Version compatibility check
MIN_PYTHON_VERSION = (3, 7)
if sys.version_info < MIN_PYTHON_VERSION:
    raise RuntimeError(f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or higher is required")

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
                "remove_empty": ("BOOLEAN", {"default": True})
            }
        }
    
    FUNCTION = "split_text"
    CATEGORY = "vsaan212/Utilities"


    # For dynamic outputs, we need to handle this differently
    # The node will always show the maximum number of outputs
    # but only the first num_splits + 1 will contain data
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text_1", "text_2", "text_3", "text_4", "text_5", "text_6", "text_7", "text_8", "remainder")
    
    def split_text(self, text: str, separator: str = "|", num_splits: int = 2, 
                   trim_whitespace: bool = True, remove_empty: bool = True) -> Tuple[str, ...]:
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
        
        # Handle regex separators (if separator starts with / and ends with /)
        if separator.startswith('/') and separator.endswith('/'):
            pattern = separator[1:-1]  # Remove the / / delimiters
            # Unescape the pattern for regex
            pattern = pattern.replace('\\\\', '\\')
            parts = re.split(pattern, text)
        else:
            # Simple string split
            parts = text.split(separator)
        
        # Process parts
        processed_parts = []
        for part in parts:
            if trim_whitespace:
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
    

