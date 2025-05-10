"""
Command line interface for Quantum Analyzer.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .analyzer import ProjectAnalyzer, PatternLoader
from .config import load_config, merge_with_args, Severity, OutputFormat
from .fix import apply_fixes


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Quantum Analyzer - Code analysis toolkit")
    
    parser.add_argument(
        "project_path", 
        type=Path,
        help="Path to the project to analyze"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--patterns", "-p",
        type=Path,
        nargs="+",
        help="YAML files containing regex patterns and improvement ideas"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Path where to save the analysis results"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "markdown", "md", "both"],
        help="Output format"
    )
    
    parser.add_argument(
        "--severity", "-s",
        choices=["info", "warning", "critical"],
        help="Minimum severity level to include"
    )
    
    parser.add_argument(
        "--tags", "-t",
        nargs="+",
        help="Only include patterns with these tags"
    )
    
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Analyze files sequentially (default: parallel)"
    )
    
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of threads to use (default: CPU count)"
    )
    
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply auto-fixes to the code"
    )
    
    parser.add_argument(
        "--fix-patterns",
        nargs="+",
        help="Fixers to apply"
    )
    
    return parser.parse_args(args)


def main() -> int:
    """Main entry point."""
    # Print banner
    print(f"Quantum Analyzer v{__import__('quantum_analyzer').__version__}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Parse arguments
    args = parse_args()
    
    start_time = time.time()
    
    try:
        # Load configuration
        config = load_config(args.config)
        config = merge_with_args(config, args)
        
        # Validate project path
        if not config.project_path.exists():
            print(f"Error: Project path {config.project_path} does not exist")
            return 1
        
        # Load patterns
        if not config.patterns:
            # If no patterns specified, use default pattern files
            from .default_patterns import IMPROVEMENT_PATTERNS, EXTENDED_IMPROVEMENT_PATTERNS
            from pathlib import Path
            import yaml
            
            patterns_dir = Path("patterns")
            patterns_dir.mkdir(exist_ok=True)
            
            base_patterns_path = patterns_dir / "base_patterns.yaml"
            extended_patterns_path = patterns_dir / "extended_patterns.yaml"
            
            # Create default pattern files if they don't exist
            if not base_patterns_path.exists():
                print(f"Creating default base patterns file: {base_patterns_path}")
                with open(base_patterns_path, "w", encoding="utf-8") as f:
                    yaml.dump({k: {"severity": "info", "tags": [], "ideas": v} 
                              for k, v in IMPROVEMENT_PATTERNS.items()}, f, sort_keys=False, indent=2)
            
            if not extended_patterns_path.exists():
                print(f"Creating default extended patterns file: {extended_patterns_path}")
                with open(extended_patterns_path, "w", encoding="utf-8") as f:
                    yaml.dump({k: {"severity": "info", "tags": [], "ideas": v} 
                              for k, v in EXTENDED_IMPROVEMENT_PATTERNS.items()}, f, sort_keys=False, indent=2)
            
            config.patterns = [base_patterns_path, extended_patterns_path]
        
        # Load patterns
        patterns = PatternLoader.load_multiple(config.patterns)
        print(f"Loaded {len(patterns)} patterns from {len(config.patterns)} files")
        
        # Create analyzer
        analyzer = ProjectAnalyzer(
            project_path=config.project_path,
            patterns=patterns,
            min_severity=config.severity,
            selected_tags=config.tags,
            parallel=config.parallel,
            threads=config.threads
        )
        
        # Run analysis
        results = analyzer.analyze()
        
        # Save results
        if config.format in (OutputFormat.JSON, OutputFormat.BOTH):
            results.save_json(config.output)
            print(f"Results saved as JSON: {config.output}")
        
        if config.format in (OutputFormat.MARKDOWN, OutputFormat.BOTH):
            md_output = config.output.with_suffix(".md")
            results.save_markdown(md_output)
            print(f"Results saved as Markdown: {md_output}")
        
        # Apply fixes if requested
        if config.fix and config.fix_patterns:
            print("\nApplying fixes...")
            total_fixes = 0
            
            # Get all Python files
            python_files = list(config.project_path.rglob("*.py"))
            
            for file_path in python_files:
                fixes = apply_fixes(file_path, config.fix_patterns)
                if fixes > 0:
                    print(f"Applied {fixes} fixes to {file_path.relative_to(config.project_path)}")
                    total_fixes += fixes
            
            print(f"\nTotal fixes applied: {total_fixes}")
        
        elapsed = time.time() - start_time
        print(f"\nAnalysis completed in {elapsed:.2f} seconds")
        return 0
    
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        return 130
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())