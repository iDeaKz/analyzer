"""
Configuration management for Quantum Analyzer.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import yaml


class OutputFormat(str, Enum):
    """Output format options."""
    JSON = "json"
    MARKDOWN = "md"
    BOTH = "both"


class Severity(str, Enum):
    """Severity levels for improvement suggestions."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AnalyzerConfig:
    """Configuration for the Quantum Analyzer."""
    
    # Patterns
    patterns: List[Path] = field(default_factory=list)
    
    # Output options
    output: Path = Path("analysis_results.json")
    format: OutputFormat = OutputFormat.JSON
    
    # Filter options
    severity: Severity = Severity.INFO
    tags: Optional[List[str]] = None
    
    # Processing options
    parallel: bool = True
    threads: int = 0  # 0 means auto (use CPU count)
    
    # Auto-fix options
    fix: bool = False
    fix_patterns: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AnalyzerConfig":
        """Create a config object from a dictionary."""
        # Convert plain paths to Path objects
        if "patterns" in config_dict:
            config_dict["patterns"] = [Path(p) for p in config_dict["patterns"]]
        
        if "output" in config_dict:
            config_dict["output"] = Path(config_dict["output"])
        
        # Convert string enums to enum values
        if "format" in config_dict:
            config_dict["format"] = OutputFormat(config_dict["format"])
        
        if "severity" in config_dict:
            config_dict["severity"] = Severity(config_dict["severity"])
        
        # Create and return the config object
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})


def load_config(path: Optional[Union[str, Path]] = None) -> AnalyzerConfig:
    """
    Load configuration from a YAML file.
    
    Args:
        path: Path to the config file. If None, search for default locations.
        
    Returns:
        AnalyzerConfig object with the loaded configuration.
    """
    # Default configuration
    config = AnalyzerConfig()
    
    # Search for config file in priority order
    if path is None:
        # Check environment variable
        env_path = os.getenv("QA_CONFIG")
        if env_path and Path(env_path).exists():
            path = env_path
        # Check current directory
        elif Path("quantum_analyzer.yaml").exists():
            path = "quantum_analyzer.yaml"
        elif Path("quantum_analyzer.yml").exists():
            path = "quantum_analyzer.yml"
    
    # If no config file found, return default config
    if path is None:
        return config
    
    # Load config from file
    try:
        with open(path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        # Update config with loaded values
        if config_dict:
            config = AnalyzerConfig.from_dict(config_dict)
    
    except Exception as e:
        print(f"Error loading config from {path}: {e}")
    
    return config


def merge_with_args(config: AnalyzerConfig, args: Any) -> AnalyzerConfig:
    """
    Merge command line arguments with configuration.
    Command line arguments take precedence over config file.
    
    Args:
        config: AnalyzerConfig object from config file
        args: Namespace object from argparse
        
    Returns:
        Updated AnalyzerConfig object
    """
    # Convert args namespace to dictionary
    args_dict = vars(args)
    
    # Only update values that are explicitly set in args
    for key, value in args_dict.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)
    
    return config