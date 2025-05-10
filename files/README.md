# Quantum Code Analyzer

A modular, extensible code analysis toolkit that scans Python codebases and suggests targeted improvements based on pattern matching.

## Features

- **Pattern-Based Analysis**: Uses regex patterns to identify code constructs and suggest improvements
- **Modular Pattern Definitions**: Patterns are defined in YAML files for easy maintenance and customization
- **Severity Levels**: Each pattern can have a severity level (info, warning, critical)
- **Tag-Based Filtering**: Patterns can be tagged and filtered by tag
- **Parallel Processing**: Analyze multiple files in parallel for faster results
- **Multiple Output Formats**: Save results as JSON or Markdown
- **Extensible Architecture**: Easy to extend with new patterns or output formats

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
python quantum_analyzer.py /path/to/your/project
```

This will analyze the project using the default patterns and save the results as JSON.

Advanced usage:

```bash
python quantum_analyzer.py /path/to/your/project \
    --patterns patterns/base_patterns.yaml patterns/security_patterns.yaml \
    --output results.json \
    --format both \
    --severity warning \
    --tags security performance
```

This will:
- Analyze the project using the specified pattern files
- Save the results as both JSON and Markdown
- Only include patterns with severity WARNING or higher
- Only include patterns tagged with "security" or "performance"

## Pattern Files

Pattern files are YAML files that define regex patterns and associated improvement ideas:

```yaml
"def\s+\w+\([^)]*\):$":
  severity: info
  tags:
    - function
    - signature
  ideas:
    - "Use explicit return type hints for better API introspection and editor support."
    - "Auto-generate OpenAPI doc summaries from function metadata."
    - "Apply decorator-based logging for entry/exit diagnostics."
```

## Output Example

JSON output:

```json
{
  "main.py": {
    "10": {
      "line": "def current_signal():",
      "ideas": [
        "Use explicit return type hints for better API introspection and editor support.",
        "Auto-generate OpenAPI doc summaries from function metadata.",
        "Apply decorator-based logging for entry/exit diagnostics."
      ],
      "severity": "info",
      "tags": ["function", "signature"]
    }
  }
}
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Add new pattern files for different types of code analysis
- Improve existing patterns
- Add new output formats
- Improve the performance of the analyzer

## License

MIT