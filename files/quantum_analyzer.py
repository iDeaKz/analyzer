#!/usr/bin/env python3
"""
Quantum Code Analyzer

A modular, extensible code analysis toolkit that scans Python codebases
and suggests targeted improvements based on pattern matching.

Usage:
    python quantum_analyzer.py [path_to_project] --patterns [pattern_files] --output [output_file]

Example:
    python quantum_analyzer.py /path/to/project --patterns patterns/base.yaml patterns/security.yaml --output analysis.json
"""

import argparse
import concurrent.futures
import json
import logging
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Union, Any

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Severity levels for improvement suggestions."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ImprovementPattern:
    """Represents a pattern to match in code and associated improvement ideas."""
    regex: str
    ideas: List[str]
    severity: Severity = Severity.INFO
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and compile the regex pattern."""
        try:
            self.compiled_regex = re.compile(self.regex)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{self.regex}': {e}")
    
    def matches(self, line: str) -> bool:
        """Check if the pattern matches a line of code."""
        return bool(self.compiled_regex.search(line))


@dataclass
class CodeLine:
    """Represents a line of code with its improvement ideas."""
    line: str
    ideas: List[str]
    severity: Severity = Severity.INFO
    tags: List[str] = field(default_factory=list)


class PatternLoader:
    """Loads and manages improvement patterns from YAML files."""
    
    @staticmethod
    def load_from_yaml(yaml_path: Path) -> List[ImprovementPattern]:
        """Load patterns from a YAML file."""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            patterns = []
            for regex, pattern_data in data.items():
                # Handle both formats: simple list of ideas or structured with severity
                if isinstance(pattern_data, list):
                    patterns.append(ImprovementPattern(
                        regex=regex,
                        ideas=pattern_data,
                        severity=Severity.INFO,
                        tags=[]
                    ))
                elif isinstance(pattern_data, dict):
                    severity = Severity(pattern_data.get('severity', 'info'))
                    patterns.append(ImprovementPattern(
                        regex=regex,
                        ideas=pattern_data['ideas'],
                        severity=severity,
                        tags=pattern_data.get('tags', [])
                    ))
                else:
                    logger.warning(f"Invalid pattern format for {regex}")
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error loading patterns from {yaml_path}: {e}")
            return []
    
    @classmethod
    def load_multiple(cls, yaml_paths: List[Path]) -> List[ImprovementPattern]:
        """Load patterns from multiple YAML files."""
        all_patterns = []
        for path in yaml_paths:
            all_patterns.extend(cls.load_from_yaml(path))
        return all_patterns


class CodeAnalyzer:
    """Analyzes Python code files for improvement opportunities."""
    
    def __init__(
        self, 
        patterns: List[ImprovementPattern],
        min_severity: Severity = Severity.INFO,
        selected_tags: Optional[List[str]] = None
    ):
        """
        Initialize the analyzer with patterns and filters.
        
        Args:
            patterns: List of patterns to match against code
            min_severity: Minimum severity level to include
            selected_tags: If provided, only include patterns with these tags
        """
        self.patterns = patterns
        self.min_severity = min_severity
        self.selected_tags = set(selected_tags) if selected_tags else None
        
        # Map severity levels to numeric values for comparison
        self.severity_values = {
            Severity.INFO: 0,
            Severity.WARNING: 1,
            Severity.CRITICAL: 2
        }
    
    def _should_include_pattern(self, pattern: ImprovementPattern) -> bool:
        """Check if a pattern should be included based on severity and tags."""
        # Check severity
        if self.severity_values[pattern.severity] < self.severity_values[self.min_severity]:
            return False
        
        # Check tags if filtering is active
        if self.selected_tags and not (set(pattern.tags) & self.selected_tags):
            return False
            
        return True
    
    def analyze_line(self, line: str) -> List[CodeLine]:
        """
        Analyze a single line of code.
        
        Args:
            line: The line of code to analyze
            
        Returns:
            List of CodeLine objects with improvement ideas
        """
        results = []
        
        line = line.strip()
        if not line or line.startswith('#'):
            return results
        
        for pattern in self.patterns:
            if not self._should_include_pattern(pattern):
                continue
                
            if pattern.matches(line):
                results.append(CodeLine(
                    line=line,
                    ideas=pattern.ideas.copy(),
                    severity=pattern.severity,
                    tags=pattern.tags.copy()
                ))
        
        return results
    
    def analyze_file(self, file_path: Path) -> Dict[int, CodeLine]:
        """
        Analyze a Python file and return improvement suggestions.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary mapping line numbers to CodeLine objects
        """
        results = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_results = self.analyze_line(line)
                if line_results:
                    # Take the first match to avoid duplicates
                    results[line_num] = line_results[0]
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return results


class AnalysisResults:
    """Stores and manages analysis results."""
    
    def __init__(self):
        """Initialize empty results container."""
        self.results = defaultdict(dict)
    
    def add_file_results(self, file_path: Path, file_results: Dict[int, CodeLine]):
        """
        Add analysis results for a file.
        
        Args:
            file_path: Path to the analyzed file
            file_results: Dictionary mapping line numbers to CodeLine objects
        """
        if not file_results:
            return
            
        str_path = str(file_path)
        for line_num, code_line in file_results.items():
            self.results[str_path][line_num] = {
                'line': code_line.line,
                'ideas': code_line.ideas,
                'severity': code_line.severity,
                'tags': code_line.tags
            }
    
    def to_dict(self) -> Dict:
        """Convert results to a dictionary that can be serialized to JSON."""
        return dict(self.results)
    
    def save_json(self, output_path: Path):
        """
        Save results as JSON.
        
        Args:
            output_path: Path where to save the results
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def save_markdown(self, output_path: Path):
        """
        Save results as Markdown.
        
        Args:
            output_path: Path where to save the results
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Code Analysis Results\n\n")
            f.write(f"_Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n")
            
            for file_path, lines in self.results.items():
                f.write(f"## {file_path}\n\n")
                
                for line_num, data in sorted(lines.items()):
                    severity = data.get('severity', 'info')
                    severity_emoji = {
                        'info': '📝',
                        'warning': '⚠️',
                        'critical': '🔥'
                    }.get(severity, '📝')
                    
                    f.write(f"### {severity_emoji} Line {line_num}\n\n")
                    f.write("```python\n")
                    f.write(f"{data['line']}\n")
                    f.write("```\n\n")
                    
                    f.write("#### Improvement Ideas\n\n")
                    for idea in data['ideas']:
                        f.write(f"- {idea}\n")
                    
                    f.write("\n")


class ProjectAnalyzer:
    """Manages the analysis of an entire project."""
    
    def __init__(
        self, 
        project_path: Path,
        patterns: List[ImprovementPattern],
        min_severity: Severity = Severity.INFO,
        selected_tags: Optional[List[str]] = None,
        parallel: bool = True
    ):
        """
        Initialize the project analyzer.
        
        Args:
            project_path: Path to the project to analyze
            patterns: List of patterns to match against code
            min_severity: Minimum severity level to include
            selected_tags: If provided, only include patterns with these tags
            parallel: Whether to analyze files in parallel
        """
        self.project_path = project_path
        self.code_analyzer = CodeAnalyzer(patterns, min_severity, selected_tags)
        self.results = AnalysisResults()
        self.parallel = parallel
    
    def get_python_files(self) -> List[Path]:
        """Get all Python files in the project."""
        return list(self.project_path.rglob("*.py"))
    
    def analyze_file_worker(self, file_path: Path) -> tuple:
        """Worker function for analyzing a file in parallel."""
        relative_path = file_path.relative_to(self.project_path)
        file_results = self.code_analyzer.analyze_file(file_path)
        return (relative_path, file_results)
    
    def analyze(self) -> AnalysisResults:
        """
        Analyze the entire project.
        
        Returns:
            AnalysisResults object containing all analysis results
        """
        start_time = time.time()
        python_files = self.get_python_files()
        
        logger.info(f"Analyzing {len(python_files)} Python files in {self.project_path}")
        
        if self.parallel:
            # Parallel analysis
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for relative_path, file_results in executor.map(self.analyze_file_worker, python_files):
                    self.results.add_file_results(relative_path, file_results)
        else:
            # Sequential analysis
            for file_path in python_files:
                relative_path = file_path.relative_to(self.project_path)
                file_results = self.code_analyzer.analyze_file(file_path)
                self.results.add_file_results(relative_path, file_results)
        
        elapsed = time.time() - start_time
        logger.info(f"Analysis completed in {elapsed:.2f} seconds")
        
        return self.results


def convert_patterns_to_yaml(patterns: Dict[str, List[str]], output_path: Path):
    """
    Convert a dictionary of patterns to YAML format.
    
    Args:
        patterns: Dictionary mapping regex patterns to lists of ideas
        output_path: Path where to save the YAML file
    """
    # Convert to structured format with severity and tags
    structured_patterns = {}
    
    for regex, ideas in patterns.items():
        structured_patterns[regex] = {
            'severity': 'info',
            'tags': [],
            'ideas': ideas
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(structured_patterns, f, sort_keys=False, indent=2)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Quantum Code Analyzer")
    
    parser.add_argument(
        "project_path", 
        type=Path,
        help="Path to the project to analyze"
    )
    
    parser.add_argument(
        "--patterns", "-p",
        type=Path,
        nargs="+",
        default=[],
        help="YAML files containing regex patterns and improvement ideas"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("code_analysis_results.json"),
        help="Path where to save the analysis results"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "md", "both"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--severity", "-s",
        choices=["info", "warning", "critical"],
        default="info",
        help="Minimum severity level to include (default: info)"
    )
    
    parser.add_argument(
        "--tags", "-t",
        nargs="+",
        default=None,
        help="Only include patterns with these tags"
    )
    
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Analyze files sequentially (default: parallel)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Create default pattern files if not provided
    if not args.patterns:
        from default_patterns import IMPROVEMENT_PATTERNS, EXTENDED_IMPROVEMENT_PATTERNS
        
        patterns_dir = Path("patterns")
        patterns_dir.mkdir(exist_ok=True)
        
        base_patterns_path = patterns_dir / "base_patterns.yaml"
        extended_patterns_path = patterns_dir / "extended_patterns.yaml"
        
        if not base_patterns_path.exists():
            logger.info(f"Creating default base patterns file: {base_patterns_path}")
            convert_patterns_to_yaml(IMPROVEMENT_PATTERNS, base_patterns_path)
        
        if not extended_patterns_path.exists():
            logger.info(f"Creating default extended patterns file: {extended_patterns_path}")
            convert_patterns_to_yaml(EXTENDED_IMPROVEMENT_PATTERNS, extended_patterns_path)
        
        args.patterns = [base_patterns_path, extended_patterns_path]
    
    # Load patterns
    patterns = PatternLoader.load_multiple(args.patterns)
    logger.info(f"Loaded {len(patterns)} patterns from {len(args.patterns)} files")
    
    # Create analyzer
    analyzer = ProjectAnalyzer(
        project_path=args.project_path,
        patterns=patterns,
        min_severity=Severity(args.severity),
        selected_tags=args.tags,
        parallel=not args.sequential
    )
    
    # Run analysis
    results = analyzer.analyze()
    
    # Save results
    if args.format in ("json", "both"):
        results.save_json(args.output)
        logger.info(f"Results saved as JSON: {args.output}")
    
    if args.format in ("markdown", "md", "both"):
        md_output = args.output.with_suffix(".md")
        results.save_markdown(md_output)
        logger.info(f"Results saved as Markdown: {md_output}")


if __name__ == "__main__":
    logger.info(f"Quantum Code Analyzer - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    logger.info("Analysis completed successfully")