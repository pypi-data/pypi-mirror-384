"""
Path management utilities for coverage tools.

Provides centralized path management and validation for the coverage system.
"""

import os
from pathlib import Path
# No typing imports needed for Python 3.11+ union syntax

from .logging_config import get_logger


class PathManager:
    """Manages paths and directories for the coverage system."""

    def __init__(self, build_root: Path | None = None, pydcov_dir: Path | None = None):
        self.logger = get_logger()

        if build_root is None:
            # Auto-detect build root by looking for CMakeCache.txt in current directory
            current = Path.cwd()

            # Check if current directory is a build directory
            if (current / 'CMakeCache.txt').exists():
                build_root = current
            else:
                raise ValueError(
                    f"Could not auto-detect CMake build directory. "
                    f"Current directory '{current}' does not contain CMakeCache.txt. "
                    f"Please specify --build-root parameter or run from a CMake build directory."
                )

        self.build_root = Path(build_root).resolve()

        # Set up pydcov_dir (separate from build_root)
        if pydcov_dir is None:
            # Default to current working directory if not specified
            pydcov_dir = Path.cwd() / 'pydcov_dir'

        self.pydcov_dir = Path(pydcov_dir).resolve()

        # For backward compatibility, keep coverage_dir pointing to the old location
        # This will be used by legacy code paths
        self.coverage_dir = self.build_root / 'coverage'

        self.logger.debug(f"Build root: {self.build_root}")
        self.logger.debug(f"PyDCov directory: {self.pydcov_dir}")
        self.logger.debug(f"Legacy coverage directory: {self.coverage_dir}")

        # Backward compatibility: provide build_dir as alias for build_root
        self.build_dir = self.build_root
    
    def ensure_coverage_dir(self) -> Path:
        """Ensure coverage directory exists and return its path."""
        self.coverage_dir.mkdir(parents=True, exist_ok=True)
        return self.coverage_dir

    def ensure_pydcov_dir(self) -> Path:
        """Ensure pydcov directory exists and return its path."""
        self.pydcov_dir.mkdir(parents=True, exist_ok=True)
        return self.pydcov_dir

    def ensure_incremental_dir(self) -> Path:
        """Ensure incremental coverage directory exists and return its path."""
        incremental_dir = self.coverage_dir / 'incremental'
        incremental_dir.mkdir(parents=True, exist_ok=True)
        return incremental_dir
    
    def get_module_coverage_dir(self, module: str) -> Path:
        """Get coverage directory for a specific module."""
        module_dir = self.coverage_dir / module
        module_dir.mkdir(parents=True, exist_ok=True)
        return module_dir
    
    def validate_build_dir(self) -> bool:
        """Check if build directory exists and contains CMake files."""
        if not self.build_root.exists():
            self.logger.error(f"Build directory not found: {self.build_root}")
            return False

        cmake_cache = self.build_root / 'CMakeCache.txt'
        if not cmake_cache.exists():
            self.logger.error(f"CMakeCache.txt not found in {self.build_root}")
            self.logger.error("Please run CMake configuration first")
            return False

        return True
    
    def validate_coverage_build(self) -> bool:
        """Check if build was configured with coverage enabled."""
        if not self.validate_build_dir():
            return False

        cmake_cache = self.build_root / 'CMakeCache.txt'
        try:
            with open(cmake_cache, 'r') as f:
                content = f.read()
                # Check for PyDCov coverage marker
                if 'PYDCOV_COVERAGE_ENABLED:BOOL=ON' in content:
                    return True
                else:
                    self.logger.error("Coverage not enabled in CMake configuration")
                    self.logger.error("Please reconfigure with: PYDCOV_ENABLE_COVERAGE=1 cmake ..")
                    return False
        except Exception as e:
            self.logger.error(f"Failed to read CMakeCache.txt: {e}")
            return False
    

    
    def clean_coverage_data(self, incremental_only: bool = False):
        """
        Clean coverage data files.

        Args:
            incremental_only: If True, only clean incremental data
        """
        if incremental_only:
            # Clean only incremental data
            incremental_dir = self.coverage_dir / 'incremental'
            if incremental_dir.exists():
                import shutil
                shutil.rmtree(incremental_dir)
                self.logger.info("Cleaned incremental coverage data")
        else:
            # Clean all coverage data
            if self.coverage_dir.exists():
                import shutil
                shutil.rmtree(self.coverage_dir)
                self.logger.info("Cleaned all coverage data")

    def clean_pydcov_data(self):
        """
        Clean all pydcov directory data.
        """
        if self.pydcov_dir.exists():
            import shutil
            shutil.rmtree(self.pydcov_dir)
            self.logger.info(f"Cleaned pydcov directory: {self.pydcov_dir}")
    
    def relative_to_build(self, path: Path) -> str:
        """Get path relative to build root."""
        try:
            return str(path.relative_to(self.build_root))
        except ValueError:
            return str(path)
