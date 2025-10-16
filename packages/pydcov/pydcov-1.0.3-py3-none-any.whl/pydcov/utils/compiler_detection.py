"""
Compiler detection and configuration utilities.

Provides automatic detection of available compilers (GCC, Clang)
and their associated coverage tools (gcov, llvm-cov, lcov).
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from pydcov.utils.logging_config import get_logger


class CompilerDetector:
    """Detects available compilers and coverage tools."""
    
    def __init__(self):
        self.logger = get_logger()
        self._cache = {}
    
    def detect_compiler(self) -> str:
        """
        Detect the primary compiler being used.

        Returns:
            'gcc' or 'clang'
        """
        if 'compiler' in self._cache:
            return self._cache['compiler']

        # First try to detect from CMake cache (most reliable)
        compiler = self._detect_from_cmake_cache()
        if compiler:
            self._cache['compiler'] = compiler
            self.logger.info(f"Detected compiler from CMake cache: {compiler}")
            return compiler

        # Fallback to system detection
        compiler = self._detect_from_system()
        self._cache['compiler'] = compiler
        self.logger.info(f"Detected compiler from system: {compiler}")
        return compiler

    def _detect_from_cmake_cache(self) -> str | None:
        """
        Detect compiler from CMake cache file and configuration log.

        Returns:
            'gcc', 'clang', or None if not found
        """
        try:
            # Look for CMake files in common locations
            base_paths = [
                Path.cwd(),
                Path.cwd() / 'build',
                Path.cwd().parent / 'build',
            ]

            for base_path in base_paths:
                # Try CMakeCache.txt first
                cache_path = base_path / 'CMakeCache.txt'
                if cache_path.exists():
                    result = self._parse_cmake_cache(cache_path)
                    if result:
                        return result

                # Try CMake configuration log
                config_log_path = base_path / 'CMakeFiles' / 'CMakeConfigureLog.yaml'
                if config_log_path.exists():
                    result = self._parse_cmake_config_log(config_log_path)
                    if result:
                        return result

        except Exception as e:
            self.logger.debug(f"Failed to read CMake files: {e}")

        return None

    def _parse_cmake_cache(self, cache_path: Path) -> str | None:
        """Parse CMake cache file to determine compiler."""
        try:
            with open(cache_path, 'r') as f:
                content = f.read()

            # Look for CMAKE_C_COMPILER_ID or CMAKE_CXX_COMPILER_ID
            import re

            # Check for compiler ID patterns
            patterns = [
                r'CMAKE_C_COMPILER_ID:INTERNAL=(\w+)',
                r'CMAKE_CXX_COMPILER_ID:INTERNAL=(\w+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    compiler_id = match.group(1).lower()
                    if 'clang' in compiler_id or 'appleclang' in compiler_id:
                        return 'clang'
                    elif 'gnu' in compiler_id or 'gcc' in compiler_id:
                        return 'gcc'

            # Also check compiler paths
            compiler_patterns = [
                r'CMAKE_C_COMPILER:FILEPATH=([^\n]+)',
                r'CMAKE_CXX_COMPILER:FILEPATH=([^\n]+)',
            ]

            for pattern in compiler_patterns:
                match = re.search(pattern, content)
                if match:
                    compiler_path = match.group(1).lower()
                    if 'clang' in compiler_path:
                        return 'clang'
                    elif 'gcc' in compiler_path:
                        return 'gcc'

        except Exception as e:
            self.logger.debug(f"Failed to parse CMake cache {cache_path}: {e}")

        return None

    def _parse_cmake_config_log(self, config_log_path: Path) -> str | None:
        """Parse CMake configuration log to determine compiler."""
        try:
            with open(config_log_path, 'r') as f:
                content = f.read()

            # Look for compiler identification messages
            import re

            # Pattern to match compiler identification lines
            patterns = [
                r'The C compiler identification is (\w+)',
                r'The CXX compiler identification is (\w+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    compiler_id = match.group(1).lower()
                    if 'clang' in compiler_id or 'appleclang' in compiler_id:
                        return 'clang'
                    elif 'gnu' in compiler_id or 'gcc' in compiler_id:
                        return 'gcc'

        except Exception as e:
            self.logger.debug(f"Failed to parse CMake config log {config_log_path}: {e}")

        return None

    def _detect_from_system(self) -> str:
        """
        Detect compiler from system availability.

        Returns:
            'gcc' or 'clang'
        """
        # Check for gcc first
        if shutil.which('gcc'):
            try:
                result = subprocess.run(
                    ['gcc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if 'clang' in result.stdout.lower():
                    return 'clang'
                else:
                    return 'gcc'
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                return 'gcc'  # Assume gcc if version check fails
        elif shutil.which('clang'):
            return 'clang'
        else:
            self.logger.error("No suitable compiler found (gcc or clang)")
            raise RuntimeError("No compiler found")
    
    def find_coverage_tools(self, compiler: str | None = None) -> Dict[str, str | None]:
        """
        Find coverage tools for the specified compiler.
        
        Args:
            compiler: Compiler type ('gcc' or 'clang'). Auto-detected if None.
            
        Returns:
            Dictionary mapping tool names to their paths
        """
        if compiler is None:
            compiler = self.detect_compiler()
        
        cache_key = f'tools_{compiler}'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        tools = {}
        
        if compiler == 'clang':
            tools.update(self._find_clang_tools())
        else:  # gcc
            tools.update(self._find_gcc_tools())
        
        self._cache[cache_key] = tools
        return tools
    
    def _find_clang_tools(self) -> Dict[str, str | None]:
        """Find Clang coverage tools."""
        tools = {}
        
        # Try to find llvm-profdata
        tools['llvm_profdata'] = self._find_llvm_tool('llvm-profdata')
        
        # Try to find llvm-cov
        tools['llvm_cov'] = self._find_llvm_tool('llvm-cov')
        
        return tools
    
    def _find_gcc_tools(self) -> Dict[str, str | None]:
        """Find GCC coverage tools."""
        tools = {}
        
        # Find gcov
        tools['gcov'] = shutil.which('gcov')
        
        # Find lcov
        tools['lcov'] = shutil.which('lcov')
        
        # Find genhtml
        tools['genhtml'] = shutil.which('genhtml')
        
        return tools
    
    def _find_llvm_tool(self, tool_name: str) -> str | None:
        """
        Find an LLVM tool, checking common installation paths.
        
        Args:
            tool_name: Name of the LLVM tool to find
            
        Returns:
            Path to the tool or None if not found
        """
        # Check PATH first
        tool_path = shutil.which(tool_name)
        if tool_path:
            return tool_path
        
        # Common LLVM installation paths
        common_paths = [
            '/opt/homebrew/Cellar/llvm/*/bin',
            '/opt/homebrew/bin',
            '/usr/local/bin',
            '/usr/bin',
            '/usr/local/opt/llvm/bin'
        ]
        
        for path_pattern in common_paths:
            if '*' in path_pattern:
                # Handle glob patterns
                import glob
                for expanded_path in glob.glob(path_pattern):
                    tool_path = Path(expanded_path) / tool_name
                    if tool_path.is_file() and os.access(tool_path, os.X_OK):
                        return str(tool_path)
            else:
                tool_path = Path(path_pattern) / tool_name
                if tool_path.is_file() and os.access(tool_path, os.X_OK):
                    return str(tool_path)
        
        return None
    
    def get_coverage_flags(self, compiler: str | None = None) -> List[str]:
        """
        Get compiler flags for coverage instrumentation.
        
        Args:
            compiler: Compiler type. Auto-detected if None.
            
        Returns:
            List of compiler flags
        """
        if compiler is None:
            compiler = self.detect_compiler()
        
        if compiler == 'clang':
            return ['-fprofile-instr-generate', '-fcoverage-mapping']
        else:  # gcc
            return ['--coverage', '-fprofile-arcs', '-ftest-coverage']
    
    def validate_tools(self, compiler: str | None = None) -> Tuple[bool, List[str]]:
        """
        Validate that all required coverage tools are available.
        
        Args:
            compiler: Compiler type. Auto-detected if None.
            
        Returns:
            Tuple of (is_valid, list_of_missing_tools)
        """
        if compiler is None:
            compiler = self.detect_compiler()
        
        tools = self.find_coverage_tools(compiler)
        missing = []
        
        if compiler == 'clang':
            required = ['llvm_profdata', 'llvm_cov']
            for tool in required:
                if not tools.get(tool):
                    missing.append(tool.replace('_', '-'))
        else:  # gcc
            required = ['gcov', 'lcov', 'genhtml']
            for tool in required:
                if not tools.get(tool):
                    missing.append(tool)
        
        return len(missing) == 0, missing
