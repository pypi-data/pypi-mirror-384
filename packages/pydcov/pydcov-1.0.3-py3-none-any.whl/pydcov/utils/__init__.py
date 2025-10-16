"""
Utility modules for coverage tools.

This package contains shared utilities used across all coverage tools:
- Compiler detection and configuration
- Logging setup and formatting
- Path management and validation
- CMake integration helpers
"""

from .compiler_detection import CompilerDetector
from .logging_config import setup_logging, get_logger
from .path_utils import PathManager
from .cmake_integration import CMakeHelper
from .test_executor import TestExecutor

__all__ = [
    "CompilerDetector",
    "setup_logging",
    "get_logger",
    "PathManager",
    "CMakeHelper",
    "TestExecutor"
]
