"""
PyDCov - Incremental C/C++ Code Coverage Tools

A streamlined incremental coverage tracking system for CMake-based C/C++ projects.
Provides incremental coverage collection and reporting capabilities with support
for both GCC/gcov and Clang/llvm-cov toolchains, plus CMake integration setup.

This package provides modern Python implementations for incremental coverage
analysis and reporting that integrate seamlessly with CMake build systems.

Example usage:
    from pydcov import IncrementalCoverageManager

    manager = IncrementalCoverageManager()
    manager.init()
    manager.add(["python", "-m", "pytest", "tests/"])
    manager.report()

Command-line usage:
    pydcov init
    pydcov add "python -m pytest tests/"
    pydcov report
    pydcov init-cmake
"""

__version__ = "1.0.3"
__author__ = "Ethan Li"

# Import main classes for easy access
from .core.incremental_coverage import IncrementalCoverageManager
from .utils.compiler_detection import CompilerDetector
from .utils.logging_config import setup_logging

__all__ = [
    "IncrementalCoverageManager",
    "CompilerDetector",
    "setup_logging"
]
