#!/usr/bin/env python3
"""
Unit tests for the Quantum Code Analyzer.
"""

import tempfile
import unittest
from pathlib import Path

from quantum_analyzer import (
    CodeAnalyzer, ImprovementPattern, PatternLoader, Severity
)


class TestPatternLoading(unittest.TestCase):
    """Test pattern loading from YAML files."""
    
    def test_load_from_yaml(self):
        """Test loading patterns from a YAML file."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(suffix='.yaml', mode='w+') as f:
            f.write("""
"def\s+\w+\([^)]*\):$":
  severity: info
  tags:
    - function
  ideas:
    - "Use explicit return type hints"
    - "Add docstrings"

"return\s+":
  severity: warning
  tags:
    - function
  ideas:
    - "Validate returned values"
            """)
            f.flush()
            
            # Load patterns
            patterns = PatternLoader.load_from_yaml(Path(f.name))
            
            # Check results
            self.assertEqual(len(patterns), 2)
            
            # Check first pattern
            self.assertEqual(patterns[0].regex, "def\s+\w+\([^)]*\):$")
            self.assertEqual(patterns[0].severity, Severity.INFO)
            self.assertEqual(patterns[0].tags, ['function'])
            self.assertEqual(len(patterns[0].ideas), 2)
            
            # Check second pattern
            self.assertEqual(patterns[1].regex, "return\s+")
            self.assertEqual(patterns[1].severity, Severity.WARNING)
            self.assertEqual(patterns[1].tags, ['function'])
            self.assertEqual(len(patterns[1].ideas), 1)


class TestCodeAnalysis(unittest.TestCase):
    """Test code analysis functionality."""
    
    def setUp(self):
        """Set up test patterns."""
        self.patterns = [
            ImprovementPattern(
                regex=r"def\s+\w+\([^)]*\):$",
                ideas=["Add type hints", "Add docstrings"],
                severity=Severity.INFO,
                tags=["function"]
            ),
            ImprovementPattern(
                regex=r"return\s+",
                ideas=["Validate return values"],
                severity=Severity.WARNING,
                tags=["return"]
            ),
            ImprovementPattern(
                regex=r"import\s+random",
                ideas=["Use a safer RNG"],
                severity=Severity.CRITICAL,
                tags=["import"]
            )
        ]
        
        self.analyzer = CodeAnalyzer(self.patterns)
    
    def test_analyze_line(self):
        """Test analyzing a single line of code."""
        # Test function definition
        results = self.analyzer.analyze_line("def my_function():")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].line, "def my_function():")
        self.assertEqual(results[0].ideas, ["Add type hints", "Add docstrings"])
        
        # Test return statement
        results = self.analyzer.analyze_line("return my_value")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].line, "return my_value")
        self.assertEqual(results[0].ideas, ["Validate return values"])
        
        # Test import random
        results = self.analyzer.analyze_line("import random")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].line, "import random")
        self.assertEqual(results[0].ideas, ["Use a safer RNG"])
        
        # Test line with no match
        results = self.analyzer.analyze_line("x = 42")
        self.assertEqual(len(results), 0)
    
    def test_severity_filtering(self):
        """Test filtering by severity."""
        analyzer = CodeAnalyzer(self.patterns, min_severity=Severity.WARNING)
        
        # Should not match (INFO < WARNING)
        results = analyzer.analyze_line("def my_function():")
        self.assertEqual(len(results), 0)
        
        # Should match (WARNING >= WARNING)
        results = analyzer.analyze_line("return my_value")
        self.assertEqual(len(results), 1)
        
        # Should match (CRITICAL > WARNING)
        results = analyzer.analyze_line("import random")
        self.assertEqual(len(results), 1)
    
    def test_tag_filtering(self):
        """Test filtering by tags."""
        analyzer = CodeAnalyzer(self.patterns, selected_tags=["return"])
        
        # Should not match (tag = function)
        results = analyzer.analyze_line("def my_function():")
        self.assertEqual(len(results), 0)
        
        # Should match (tag = return)
        results = analyzer.analyze_line("return my_value")
        self.assertEqual(len(results), 1)
        
        # Should not match (tag = import)
        results = analyzer.analyze_line("import random")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()