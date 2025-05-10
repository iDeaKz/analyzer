from collections import defaultdict
import os
import re
from pathlib import Path
from typing import Dict, List, Any

# Dictionary of patterns to match and corresponding improvement ideas
IMPROVEMENT_PATTERNS = {
    # Function definitions
    r"def\s+\w+\([^)]*\):$": [
        "Use explicit return type hints for better API introspection and editor support.",
        "Auto-generate OpenAPI doc summaries from function metadata.",
        "Apply decorator-based logging for entry/exit diagnostics."
    ],
    
    # Return statements
    r"return\s+": [
        "Run schema validation on returned object using `model.validate()`.",
        "Log structured metrics (e.g., reward, entropy) to a telemetry endpoint.",
        "Consider transforming objects into serializable DTOs before returning to clients."
    ],
    
    # Import random
    r"import\s+random": [
        "Refactor to support pluggable RNG modules for simulation variety (e.g., secrets or numpy).",
        "Encapsulate RNG access in a `rng_utils.py` for unit testing and mocking.",
        "Introduce entropy seed management for experiment repeatability."
    ],
    
    # Loading data from file
    r"json\.loads\(Path\([^)]+\)\.read_text\(\)\)": [
        "Move I/O to a dedicated `repository` or `storage` layer to respect clean architecture.",
        "Add structured validation using Pydantic or Marshmallow schemas for all input data.",
        "Implement fallbacks or dynamic file resolution for multi-env support."
    ],
    
    # Random choices and values
    r"random\.(choice|uniform|randint)": [
        "Make entropy ranges and options configurable via `.env` or config file.",
        "Replace magic values with constants (already done) but ensure they're externally tunable.",
        "Store generated randomness in fork logs for quantum traceability."
    ]
}

def analyze_code_files(directory_path: str) -> Dict[str, Any]:
    """
    Analyze Python files in a directory and provide improvement suggestions.
    
    Args:
        directory_path: Path to the directory containing the files to analyze
        
    Returns:
        A defaultdict containing analysis results for each file
    """
    results = defaultdict(dict)
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                
                analyze_file(file_path, relative_path, results)
    
    return results

def analyze_file(file_path: str, relative_path: str, results: defaultdict) -> None:
    """
    Analyze a single Python file and add suggestions to the results.
    
    Args:
        file_path: Absolute path to the file
        relative_path: Path relative to the base directory
        results: The results defaultdict to update
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        for pattern, ideas in IMPROVEMENT_PATTERNS.items():
            if re.search(pattern, line):
                results[relative_path][line_num] = {
                    'line': line,
                    'ideas': ideas.copy()
                }

def main():
    # Path to your project
    project_path = "/path/to/legendary_quantum_gpt_api"
    
    # Analyze the code
    results = analyze_code_files(project_path)
    
    # Print results
    print("Result")
    print(results)
    
    # Optionally save results to a JSON file
    # import json
    # with open('code_analysis_results.json', 'w') as f:
    #     json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()