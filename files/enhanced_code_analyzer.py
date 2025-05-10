from collections import defaultdict
import os
import re
from pathlib import Path
from typing import Dict, List, Any

# Basic improvement patterns as shown in the initial example
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

# Extended improvement patterns as provided by the user
EXTENDED_IMPROVEMENT_PATTERNS = {
    # 1. Class definitions
    r"class\s+\w+\([^)]*\):": [
        "Document class invariants and responsibilities in the class docstring.",
        "Apply the Single Responsibility Principle: split large classes into smaller collaborators.",
        "Annotate all attributes and methods with type hints for better static analysis."
    ],

    # 2. Decorators
    r"@\w+": [
        "Ensure each decorator has accompanying tests for both wrapped and unwrapped behavior.",
        "Use functools.wraps in your decorator implementation to preserve metadata.",
        "Validate decorator arguments and provide clear error messages on misuse."
    ],

    # 3. Function definitions (with type hints)
    r"def\s+\w+\([^)]*\)\s*->\s*\w+": [
        "Leverage `typing.Protocol` for function signatures used as callbacks.",
        "Generate OpenAPI specs automatically from annotated functions.",
        "Enforce strict mypy checks on return types in CI."
    ],

    # 4. Async functions
    r"async\s+def\s+\w+\(": [
        "Add timeouts to all async calls with `asyncio.wait_for` to avoid hangs.",
        "Group related coroutines with `asyncio.gather` for parallel execution.",
        "Ensure cancellation handling (try/except `asyncio.CancelledError`)."
    ],

    # 5. Await expressions
    r"await\s+": [
        "Wrap awaited calls in try/except to catch network or I/O errors.",
        "Consider caching results of idempotent async calls with an LRU cache.",
        "Log coroutine start/end times for performance diagnostics."
    ],

    # 6. Context managers
    r"with\s+[\w\.]+\s+as\s+\w+:": [
        "Implement custom context managers using `contextlib.contextmanager` for better readability.",
        "Ensure resources (files, DB connections) are always closed even on exceptions.",
        "Wrap multiple resources in a single `ExitStack` when needed."
    ],

    # 7. List comprehensions
    r"\[.*for.*in.*\]": [
        "For long comprehensions, switch to generator expressions to reduce memory use.",
        "Use built-in functions like `map` if it yields clearer intent.",
        "Add a conditional filter clause to guard against invalid inputs."
    ],

    # 8. Dict comprehensions
    r"\{.*:.*for.*in.*\}": [
        "Validate keys and values within comprehension to avoid silent errors.",
        "Consider `defaultdict` if you're aggregating values per key.",
        "Extract complex logic into a helper function for readability."
    ],

    # 9. f‐strings
    r"f\"[^\"]*\"": [
        "Pass all interpolated values through sanitizers or formatters to prevent injection.",
        "For multi‐line templates, use `str.format` or templating engines for maintainability.",
        "Avoid very long f-strings in code—break into smaller parts or helper functions."
    ],

    # 10. .format() usage
    r"\.format\(": [
        "Prefer f-strings in Python 3.6+ for performance and clarity.",
        "If used for localization, integrate with `gettext` for translatable strings.",
        "Validate that number of placeholders matches arguments to avoid runtime errors."
    ],

    # 11. Try/Except blocks
    r"try:|except\s+": [
        "Catch specific exception types instead of broad `except:` clauses.",
        "Log exception context with stack traces using `logging.exception()`.",
        "Use `finally` to release resources regardless of success/failure."
    ],

    # 12. Logging calls
    r"logging\.(info|debug|warning|error|critical)\(": [
        "Structure logs with JSON format for ingestion by log aggregators.",
        "Include contextual metadata (user_id, request_id) in each log record.",
        "Use `logger = logging.getLogger(__name__)` instead of the root logger."
    ],

    # 13. Raw SQL execution
    r"\.execute\(": [
        "Use parameterized queries to prevent SQL injection.",
        "Abstract raw SQL into a repository layer for testability.",
        "Log slow queries using a query profiler or DB instrumentation."
    ],

    # 14. HTTP requests (requests library)
    r"requests\.\w+\(": [
        "Wrap calls in retry logic with exponential backoff (e.g., `tenacity`).",
        "Validate HTTP response status codes and raise on errors.",
        "Use session objects (`requests.Session`) to reuse connections."
    ],

    # 15. Subprocess invocations
    r"subprocess\.\w+\(": [
        "Prefer `subprocess.run(..., capture_output=True, check=True)` for safety.",
        "Avoid shell=True; if necessary, validate all inputs to prevent shell injection.",
        "Timeout long‐running subprocesses to avoid zombie processes."
    ],

    # 16. Thread creation
    r"threading\.Thread": [
        "Use `concurrent.futures.ThreadPoolExecutor` for simpler thread pooling.",
        "Ensure threads are marked as daemon or properly joined on shutdown.",
        "Protect shared state with locks or use thread‐safe data structures."
    ],

    # 17. Multiprocessing usage
    r"multiprocessing\.\w+\(": [
        "Avoid large pickled payloads by using shared memory or managers.",
        "Set `process.daemon=True` if appropriate to avoid orphan processes.",
        "Monitor worker failures and automatically restart if needed."
    ],

    # 18. Regex operations
    r"re\.(search|match|compile)\(": [
        "Compile frequently used patterns once and reuse the compiled object.",
        "Anchor your regex (`^`/`$`) to avoid catastrophic backtracking.",
        "Provide clear error messages if the pattern fails to match."
    ],

    # 19. JSON load/dump
    r"json\.(loads|dumps)": [
        "Wrap JSON operations in try/except to catch malformed data.",
        "Use `orjson` or `ujson` for higher‐performance serialization where safe.",
        "Validate deserialized data against a schema (e.g., Pydantic)."
    ],

    # 20. YAML load
    r"yaml\.(load|safe_load)\(": [
        "Always use `safe_load` to avoid arbitrary code execution risks.",
        "Validate loaded config against a schema (e.g., `cerberus`).",
        "Cache parsed config if it's expensive to load repeatedly."
    ],

    # 21. Environment variable access
    r"os\.environ\[[\'\"]\w+[\'\"]\]": [
        "Provide default values or fail fast with clear errors on missing env vars.",
        "Centralize env‐var access in a config module for single‐point management.",
        "Validate types (e.g., int, bool) when parsing env variables."
    ],

    # 22. Argument parsing
    r"argparse\.ArgumentParser": [
        "Group related options into sub‐parsers for complex CLIs.",
        "Auto‐generate help text and usage examples.",
        "Validate mutually exclusive arguments with `add_mutually_exclusive_group`."
    ],

    # 23. Dataclass usage
    r"@dataclass": [
        "Freeze dataclasses (`@dataclass(frozen=True)`) for immutability when possible.",
        "Add `__post_init__` for validation of passed‐in values.",
        "Generate JSON serializers via `asdict()` or custom encoder hooks."
    ],

    # 24. Magic numbers
    r"\b\d+\b": [
        "Replace magic numbers with named constants or enums.",
        "Provide unit tests that document boundary conditions around numeric constants.",
        "Annotate surprising values with comments explaining their origin."
    ],

    # 25. Test definitions
    r"def\s+test_\w+\(": [
        "Use parameterized tests (`pytest.mark.parametrize`) to cover multiple scenarios.",
        "Mock external dependencies to isolate unit tests.",
        "Ensure each test has clear setup, exercise, and assertion phases."
    ],
}

# Combine both sets of patterns
ALL_PATTERNS = {**IMPROVEMENT_PATTERNS, **EXTENDED_IMPROVEMENT_PATTERNS}

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
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            for pattern, ideas in ALL_PATTERNS.items():
                if re.search(pattern, line):
                    # Avoid duplicate entries for the same line
                    if line_num not in results[relative_path]:
                        results[relative_path][line_num] = {
                            'line': line,
                            'ideas': ideas.copy()
                        }
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

def main():
    """
    Main function to run the code analyzer.
    """
    # Path to your project - update this to point to your legendary_quantum_gpt_api directory
    project_path = "/mnt/data/legendary_quantum_gpt_api"
    
    # Analyze the code
    results = analyze_code_files(project_path)
    
    # Print results
    print("Result")
    print(results)
    
    # Optionally save results to a JSON file
    import json
    with open('/mnt/data/code_analysis_results.json', 'w') as f:
        json.dump(dict(results), f, indent=2)
    
    # Also save as a pretty-printed format
    from pprint import pformat
    with open('/mnt/data/code_analysis_formatted.txt', 'w') as f:
        f.write("Result\n" + pformat(results))

if __name__ == "__main__":
    # Log current date and time
    from datetime import datetime
    print(f"Analysis started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    print(f"Analysis completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")