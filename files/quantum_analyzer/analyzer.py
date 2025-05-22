"""Wrapper module exposing ProjectAnalyzer and PatternLoader."""

from importlib import util
from pathlib import Path

# Load the implementation from the top-level quantum_analyzer.py file
_impl_path = Path(__file__).resolve().parent.parent / "quantum_analyzer.py"
_spec = util.spec_from_file_location("_qa_impl", _impl_path)
_module = util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

ProjectAnalyzer = _module.ProjectAnalyzer
PatternLoader = _module.PatternLoader
