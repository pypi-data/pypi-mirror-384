"""
CMake integration utilities for coverage tools.

Provides helpers for running CMake targets and integrating with the
existing CMake-based coverage system.
"""

import subprocess
from pathlib import Path
from typing import List

from pydcov.utils.logging_config import get_logger
from pydcov.utils.path_utils import PathManager


class CMakeHelper:
    """Helper for CMake integration and target execution."""
    
    def __init__(self, path_manager: PathManager):
        self.path_manager = path_manager
        self.logger = get_logger()
    
    def run_target(self, target: str, cwd: Path | None = None) -> bool:
        """
        Run a CMake target using make.
        
        Args:
            target: CMake target name
            cwd: Working directory (defaults to build directory)
            
        Returns:
            True if successful, False otherwise
        """
        if cwd is None:
            cwd = self.path_manager.build_dir
        
        if not self.path_manager.validate_build_dir():
            return False
        
        try:
            self.logger.debug(f"Running CMake target: {target}")
            result = subprocess.run(
                ['make', target],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.debug(f"Target {target} completed successfully")
                if result.stdout.strip():
                    self.logger.debug(f"Output: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"Target {target} failed with return code {result.returncode}")
                if result.stderr.strip():
                    self.logger.error(f"Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Target {target} timed out")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run target {target}: {e}")
            return False
        except FileNotFoundError:
            self.logger.error("Make not found. Please install build tools.")
            return False
    
    def build_project(self) -> bool:
        """Build the entire project."""
        return self.run_target('all')
    
    def ensure_build_configured(self) -> bool:
        """
        Ensure the project is properly configured for coverage.
        
        Returns:
            True if configured, False otherwise
        """
        # Create build directory if it doesn't exist
        self.path_manager.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if already configured with coverage
        if self.path_manager.validate_coverage_build():
            return True
        
        # Configure the project
        return False
    
    def get_available_targets(self) -> List[str]:
        """
        Get list of available CMake targets.
        
        Returns:
            List of target names
        """
        try:
            result = subprocess.run(
                ['make', 'help'],
                cwd=self.path_manager.build_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                targets = []
                for line in result.stdout.split('\n'):
                    if '...' in line and not line.startswith('The following'):
                        target = line.split('...')[0].strip()
                        if target:
                            targets.append(target)
                return targets
            else:
                self.logger.warning("Could not retrieve target list")
                return []
                
        except Exception as e:
            self.logger.warning(f"Failed to get targets: {e}")
            return []
