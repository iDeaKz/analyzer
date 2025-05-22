# Quantum Analyzer

A modular, extensible code analysis toolkit that scans Python codebases and suggests targeted improvements based on pattern matching.

## Features

- **Pattern-Based Analysis**: Uses regex patterns to identify code constructs and suggest improvements
- **Modular Pattern Definitions**: Patterns are defined in YAML files for easy maintenance and customization
- **Severity Levels**: Each pattern can have a severity level (info, warning, critical)
- **Tag-Based Filtering**: Patterns can be tagged and filtered by tag
- **Parallel Processing**: Analyze multiple files in parallel for faster results
- **Multiple Output Formats**: Save results as JSON or Markdown
- **Auto-Fix Capability**: Automatically apply simple fixes to code
- **Extensible Architecture**: Easy to extend with new patterns or output formats

## Installation

### From PyPI

```bash
pip install quantum-analyzer
```
