"""
Coverage tool detection and management utilities.

This module provides Python-based detection and configuration of coverage tools,
replacing the CMake-based tool detection with a more maintainable Python implementation.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydcov.utils.logging_config import get_logger


class CoverageToolManager:
    """Manages detection and configuration of coverage tools."""
    
    def __init__(self):
        self.logger = get_logger()
        self._tool_cache: Dict[str, Optional[str]] = {}
        self._compiler_cache: Optional[str] = None
    
    def detect_compiler(self) -> str:
        """
        Detect the compiler being used.
        
        Returns:
            'clang', 'gcc', or 'unknown'
        """
        if self._compiler_cache is not None:
            return self._compiler_cache
        
        # Try to detect from environment or common locations
        cc = os.environ.get('CC', 'cc')
        
        try:
            result = subprocess.run([cc, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            output = result.stdout.lower()
            
            if 'clang' in output:
                self._compiler_cache = 'clang'
            elif 'gcc' in output or 'gnu' in output:
                self._compiler_cache = 'gcc'
            else:
                self._compiler_cache = 'unknown'
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.logger.warning(f"Could not detect compiler from {cc}")
            self._compiler_cache = 'unknown'
        
        self.logger.info(f"Detected compiler: {self._compiler_cache}")
        return self._compiler_cache
    
    def find_tool(self, tool_name: str, alternatives: List[str] = None) -> Optional[str]:
        """
        Find a coverage tool executable.
        
        Args:
            tool_name: Primary tool name to search for
            alternatives: Alternative names to try
            
        Returns:
            Path to tool executable or None if not found
        """
        if tool_name in self._tool_cache:
            return self._tool_cache[tool_name]
        
        if alternatives is None:
            alternatives = []
        
        search_names = [tool_name] + alternatives
        
        # Try standard PATH search first
        for name in search_names:
            path = shutil.which(name)
            if path:
                self._tool_cache[tool_name] = path
                self.logger.debug(f"Found {tool_name} at {path}")
                return path
        
        # Platform-specific searches
        if platform.system() == 'Darwin':  # macOS
            path = self._find_tool_macos(search_names)
            if path:
                self._tool_cache[tool_name] = path
                return path
        
        # Try versioned alternatives (common on Ubuntu)
        versioned_names = []
        for name in search_names:
            for version in ['18', '17', '16', '15', '14', '13', '12']:
                versioned_names.append(f"{name}-{version}")
        
        for name in versioned_names:
            path = shutil.which(name)
            if path:
                self._tool_cache[tool_name] = path
                self.logger.debug(f"Found {tool_name} at {path} (versioned)")
                return path
        
        self.logger.warning(f"Could not find {tool_name}")
        self._tool_cache[tool_name] = None
        return None
    
    def _find_tool_macos(self, tool_names: List[str]) -> Optional[str]:
        """Find tools on macOS using xcrun."""
        xcrun = shutil.which('xcrun')
        if not xcrun:
            return None
        
        for tool_name in tool_names:
            try:
                result = subprocess.run([xcrun, '--find', tool_name],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path and Path(path).exists():
                        self.logger.debug(f"Found {tool_name} via xcrun at {path}")
                        return path
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                continue
        
        return None
    
    def get_coverage_tools(self, compiler: str = None) -> Dict[str, Optional[str]]:
        """
        Get all coverage tools for the specified compiler.
        
        Args:
            compiler: Compiler type ('clang', 'gcc', or auto-detect)
            
        Returns:
            Dictionary mapping tool names to their paths
        """
        if compiler is None:
            compiler = self.detect_compiler()
        
        tools = {}
        
        if compiler == 'clang':
            tools['llvm_profdata'] = self.find_tool('llvm-profdata')
            tools['llvm_cov'] = self.find_tool('llvm-cov')
        elif compiler == 'gcc':
            tools['gcov'] = self.find_tool('gcov')
            tools['lcov'] = self.find_tool('lcov')
            tools['genhtml'] = self.find_tool('genhtml')
        
        return tools
    
    def validate_tools(self, compiler: str = None) -> Tuple[bool, List[str]]:
        """
        Validate that required tools are available.
        
        Args:
            compiler: Compiler type to validate tools for
            
        Returns:
            Tuple of (all_found, missing_tools)
        """
        if compiler is None:
            compiler = self.detect_compiler()
        
        tools = self.get_coverage_tools(compiler)
        missing = []
        
        if compiler == 'clang':
            required = ['llvm_profdata', 'llvm_cov']
        elif compiler == 'gcc':
            required = ['gcov', 'lcov', 'genhtml']
        else:
            return False, ['unknown compiler']
        
        for tool in required:
            if not tools.get(tool):
                missing.append(tool.replace('_', '-'))
        
        return len(missing) == 0, missing
    
    def get_tool_info(self) -> Dict[str, any]:
        """Get comprehensive tool information for debugging."""
        compiler = self.detect_compiler()
        tools = self.get_coverage_tools(compiler)
        valid, missing = self.validate_tools(compiler)
        
        return {
            'compiler': compiler,
            'platform': platform.system(),
            'tools': tools,
            'valid': valid,
            'missing': missing,
            'cache': self._tool_cache.copy()
        }
