"""
Auto-fix support for Quantum Analyzer.
"""

from pathlib import Path
from typing import Dict, List, Type, Callable

# Import all fixers
from .format_to_fstring import FormatToFString


# Register all available fixers
AVAILABLE_FIXERS: Dict[str, Type] = {
    "format_to_fstring": FormatToFString,
}


def get_fixer(fixer_name: str) -> Type:
    """
    Get a fixer class by name.
    
    Args:
        fixer_name: Name of the fixer to get
        
    Returns:
        Fixer class
        
    Raises:
        ValueError: If fixer is not found
    """
    if fixer_name not in AVAILABLE_FIXERS:
        raise ValueError(f"Fixer {fixer_name} not found. Available fixers: {', '.join(AVAILABLE_FIXERS.keys())}")
    
    return AVAILABLE_FIXERS[fixer_name]


def apply_fixes(file_path: Path, fixers: List[str]) -> int:
    """
    Apply fixes to a file.
    
    Args:
        file_path: Path to the file to fix
        fixers: List of fixer names to apply
        
    Returns:
        Number of fixes applied
    """
    # Skip non-Python files
    if not file_path.name.endswith(".py"):
        return 0
    
    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return 0
    
    # Apply each fixer
    fixes_applied = 0
    for fixer_name in fixers:
        try:
            fixer_class = get_fixer(fixer_name)
            fixer = fixer_class()
            new_content, applied = fixer.apply(content)
            
            if applied > 0:
                content = new_content
                fixes_applied += applied
        
        except Exception as e:
            print(f"Error applying fixer {fixer_name} to {file_path}: {e}")
    
    # Write updated content if any fixes were applied
    if fixes_applied > 0:
        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")
            return 0
    
    return fixes_applied