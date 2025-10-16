"""
Incremental coverage manager for accumulating coverage across multiple test runs.

This module provides incremental coverage functionality equivalent to the
incremental coverage collection workflow, allowing coverage data to be
accumulated across multiple pytest executions.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from pydcov.utils.compiler_detection import CompilerDetector
from pydcov.utils.logging_config import get_logger
from pydcov.utils.path_utils import PathManager
from pydcov.utils.cmake_integration import CMakeHelper
from pydcov.utils.test_executor import TestExecutor
from pydcov.utils.coverage_file_manager import CoverageFileManager
from pydcov.utils.config import PyDCovConfig


class IncrementalCoverageManager:
    """Manages incremental coverage collection and reporting workflows."""

    def __init__(self, build_root: Path | None = None, pydcov_dir: Path | None = None, is_init_command: bool = False):
        """
        Initialize IncrementalCoverageManager.

        Args:
            build_root: Path to CMake build directory. If None, will try to load from config or auto-detect.
            pydcov_dir: Path to pydcov directory. If None, will try to load from config or default to current directory.
            is_init_command: True if this is being called from the init command
        """
        self.logger = get_logger()
        self.config = PyDCovConfig()

        # For init command, use provided build_root or auto-detect
        # For other commands, try to load from config first
        if is_init_command:
            resolved_build_root = build_root
            resolved_pydcov_dir = pydcov_dir
        else:
            # Try to load from config first
            resolved_build_root = self.config.get_build_root()
            if resolved_build_root is None and build_root is not None:
                # Fallback to provided build_root (for backward compatibility)
                resolved_build_root = build_root
            elif resolved_build_root is None:
                # No config found and no build_root provided - let PathManager handle auto-detection
                resolved_build_root = None

            # Handle pydcov_dir similarly
            resolved_pydcov_dir = self.config.get_pydcov_dir()
            if resolved_pydcov_dir is None and pydcov_dir is not None:
                resolved_pydcov_dir = pydcov_dir

        self.path_manager = PathManager(resolved_build_root, resolved_pydcov_dir)
        self.cmake_helper = CMakeHelper(self.path_manager)
        self.compiler_detector = CompilerDetector()

        self.test_executor = TestExecutor(self.logger)

        # Initialize file manager for pure Python coverage operations
        self.file_manager = CoverageFileManager(
            self.path_manager.build_dir,
            self.path_manager.pydcov_dir
        )

        # Validate tools on initialization
        self._validate_environment()

    def _create_unique_add_subdir(self) -> Path:
        """
        Create a unique subdirectory for this add operation.

        Returns:
            Path to the created unique subdirectory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        unique_dir = self.path_manager.pydcov_dir / f"add_{timestamp}"
        unique_dir.mkdir(parents=True, exist_ok=True)
        return unique_dir
    
    def _validate_environment(self):
        """Validate that required tools are available."""
        compiler = self.compiler_detector.detect_compiler()
        is_valid, missing = self.compiler_detector.validate_tools(compiler)
        
        if not is_valid:
            self.logger.error(f"Missing required coverage tools: {', '.join(missing)}")
            self.logger.error("Please install the required tools before proceeding")
            raise RuntimeError(f"Missing coverage tools: {missing}")
    
    def init(self) -> bool:
        """
        Initialize incremental coverage collection.

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Initializing incremental coverage collection...")

        # Save build root and pydcov_dir to configuration for future commands first
        if not self.config.set_build_root(self.path_manager.build_root):
            self.logger.warning("Failed to save build root configuration")
        else:
            self.logger.info(f"Build root saved to configuration: {self.path_manager.build_root}")

        if not self.config.set_pydcov_dir(self.path_manager.pydcov_dir):
            self.logger.warning("Failed to save pydcov directory configuration")
        else:
            self.logger.info(f"PyDCov directory saved to configuration: {self.path_manager.pydcov_dir}")

        # Ensure proper CMake configuration
        if not self.cmake_helper.ensure_build_configured():
            self.logger.error("CMake configuration failed, but build root has been saved")
            return False

        # Initialize incremental coverage using pure Python
        if not self.file_manager.init_incremental():
            self.logger.error("Incremental coverage initialization failed")
            return False

        self.logger.success("Incremental coverage initialized")
        return True
    
    def add(self, test_command: str | List[str], timeout: int = None) -> bool:
        """
        Run tests and add coverage data to incremental collection.

        Args:
            test_command: Test command to execute. Must be specified explicitly.
                         Examples:
                         - "python -m pytest tests/"
                         - ["python", "-m", "unittest", "discover"]
                         - "./run_tests.sh"
            timeout: Timeout in seconds for test execution (default: None, no timeout)

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Running tests and collecting coverage data...")

        # Parse and prepare test command
        if isinstance(test_command, list):
            parsed_command = TestExecutor.parse_test_command(test_command)
        else:
            parsed_command = test_command

        # Ensure build is ready
        if not self.path_manager.validate_coverage_build():
            self.logger.error("Coverage build not configured")
            return False

        # Set up environment for coverage
        env = os.environ.copy()
        compiler = self.compiler_detector.detect_compiler()

        # Create unique subdirectory for this add operation
        add_subdir = self._create_unique_add_subdir()
        self.file_manager.set_current_add_subdir(add_subdir)
        self.logger.info(f"Created unique subdirectory for this add operation: {add_subdir}")

        if compiler == 'clang':
            # Set LLVM_PROFILE_FILE for Clang coverage
            coverage_dir = self.path_manager.ensure_coverage_dir()
            env['LLVM_PROFILE_FILE'] = str(coverage_dir / 'coverage-%p-%m.profraw')
            self.logger.info(f"Using Clang coverage with LLVM_PROFILE_FILE={env['LLVM_PROFILE_FILE']}")

        # Execute test command using TestExecutor
        if not self.test_executor.execute_test_command(
            parsed_command,
            env=env,
            timeout=timeout
        ):
            return False

        # Collect all coverage files generated during testing using pure Python
        profraw_count, gcda_count = self.file_manager.collect_coverage_files()

        if profraw_count == 0 and gcda_count == 0:
            self.logger.warning("No coverage files were collected")
            return False

        # Show collection results
        self._show_collection_status()
        return True

    def _show_collection_status(self) -> None:
        """Show status of collected coverage files."""
        status = self.file_manager.get_status()

        if status['profraw_count'] > 0:
            self.logger.info(f"Collected {status['profraw_count']} Clang coverage files")
        if status['gcda_count'] > 0:
            self.logger.info(f"Collected {status['gcda_count']} GCC coverage files")

        if status['profraw_count'] == 0 and status['gcda_count'] == 0:
            self.logger.warning("No coverage files were collected")


    def merge(self) -> bool:
        """
        Merge all accumulated coverage data.

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Merging all incremental coverage data...")

        # Merge coverage data using pure Python
        compiler = self.compiler_detector.detect_compiler()
        if not self.file_manager.merge_coverage_data(compiler):
            self.logger.error("Coverage data merge failed")
            return False

        self.logger.success("Coverage data merged successfully")
        return True
    

    def report(self) -> bool:
        """
        Generate final comprehensive coverage report.

        Automatically merges coverage data if needed before generating the report.

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Generating final comprehensive coverage report...")

        # Check if merged data exists, if not, merge automatically
        compiler = self.compiler_detector.detect_compiler()
        pydcov_dir = self.path_manager.pydcov_dir

        if compiler == 'clang':
            merged_file = pydcov_dir / 'merged.profdata'
        else:  # gcc
            merged_file = pydcov_dir / 'merged.info'

        if not merged_file.exists():
            self.logger.info("Merged coverage data not found, merging automatically...")
            if not self.merge():
                self.logger.error("Automatic merge failed")
                return False

        # Generate report using pure Python
        executables = self._find_executables()

        if not self.file_manager.generate_report(compiler, executables):
            self.logger.error("Incremental coverage report generation failed")
            return False

        # Check if reports were generated
        pydcov_dir = self.path_manager.pydcov_dir
        report_dir = pydcov_dir / 'report'

        if report_dir.exists() and (report_dir / 'index.html').exists():
            self.logger.success(f"Final coverage report generated")
            self.logger.success(f"Report available at: {report_dir / 'index.html'}")
        else:
            self.logger.warning("HTML report not found, but report generation completed")

        return True

    def _find_executables(self) -> List[Path]:
        """
        Find executable files for coverage reporting by analyzing CMake build directory.

        This method uses multiple strategies to detect executables generically:
        1. Parse CMake TargetDirectories.txt to find executable targets
        2. Use 'make help' to get available targets and filter executables
        3. Scan filesystem for executable files with proper filtering

        Returns:
            List of executable paths
        """
        executables = []
        build_dir = self.path_manager.build_dir

        if not build_dir.exists():
            return executables

        # Strategy 1: Parse CMake TargetDirectories.txt to find executable targets
        cmake_executables = self._find_executables_from_cmake_targets()
        if cmake_executables:
            executables.extend(cmake_executables)
            self.logger.debug(f"Found {len(cmake_executables)} executables from CMake targets")

        # Strategy 2: Use make help to find executable targets
        if not executables:
            make_executables = self._find_executables_from_make_targets()
            if make_executables:
                executables.extend(make_executables)
                self.logger.debug(f"Found {len(make_executables)} executables from make targets")

        # Strategy 3: Fallback to filesystem scan with intelligent filtering
        if not executables:
            fs_executables = self._find_executables_from_filesystem()
            if fs_executables:
                executables.extend(fs_executables)
                self.logger.debug(f"Found {len(fs_executables)} executables from filesystem scan")

        # Remove duplicates while preserving order
        unique_executables = []
        seen = set()
        for exe in executables:
            if exe not in seen:
                unique_executables.append(exe)
                seen.add(exe)

        if unique_executables:
            self.logger.info(f"Found {len(unique_executables)} executable(s) for coverage analysis")
            for exe in unique_executables:
                self.logger.debug(f"  - {exe.relative_to(build_dir)}")
        else:
            self.logger.warning("No executables found for coverage analysis")

        return unique_executables

    def _find_executables_from_cmake_targets(self) -> List[Path]:
        """
        Find executables by parsing CMake TargetDirectories.txt file.

        Returns:
            List of executable paths found from CMake targets
        """
        executables = []
        build_dir = self.path_manager.build_dir
        target_dirs_file = build_dir / 'CMakeFiles' / 'TargetDirectories.txt'

        if not target_dirs_file.exists():
            return executables

        try:
            with open(target_dirs_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or '/CMakeFiles/' not in line:
                        continue

                    # Extract target name from path like:
                    # /path/to/build/examples/algorithm/app/CMakeFiles/algorithm_cli.dir
                    if line.endswith('.dir'):
                        target_name = Path(line).name[:-4]  # Remove .dir suffix

                        # Skip system targets
                        if target_name in ['test', 'edit_cache', 'rebuild_cache',
                                         'list_install_components', 'install', 'local', 'strip']:
                            continue

                        # Find the actual executable file
                        target_dir = Path(line).parent.parent  # Go up from CMakeFiles/target.dir
                        exe_path = target_dir / target_name

                        if exe_path.exists() and exe_path.is_file() and os.access(exe_path, os.X_OK):
                            executables.append(exe_path)

        except Exception as e:
            self.logger.debug(f"Failed to parse CMake targets: {e}")

        return executables

    def _find_executables_from_make_targets(self) -> List[Path]:
        """
        Find executables by querying make targets.

        Returns:
            List of executable paths found from make targets
        """
        executables = []
        build_dir = self.path_manager.build_dir

        try:
            import subprocess
            result = subprocess.run(
                ['make', 'help'],
                cwd=build_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return executables

            # Parse make help output to find potential executable targets
            for line in result.stdout.split('\n'):
                if line.startswith('...') and not line.startswith('The following'):
                    # Format is "... target_name (description)"
                    target_part = line[3:].strip()  # Remove "..." prefix
                    if ' ' in target_part:
                        target = target_part.split(' ')[0].strip()
                    else:
                        target = target_part.strip()

                    # Skip system targets
                    if target in ['all', 'clean', 'depend', 'edit_cache', 'install',
                                'install/local', 'install/strip', 'list_install_components',
                                'rebuild_cache', 'test']:
                        continue

                    # Look for the executable file in the build directory
                    for exe_path in build_dir.rglob(target):
                        if (exe_path.is_file() and
                            os.access(exe_path, os.X_OK) and
                            'CMakeFiles' not in str(exe_path)):
                            executables.append(exe_path)
                            break  # Only take the first match

        except Exception as e:
            self.logger.debug(f"Failed to query make targets: {e}")

        return executables

    def _find_executables_from_filesystem(self) -> List[Path]:
        """
        Find executables by scanning the filesystem with intelligent filtering.

        Returns:
            List of executable paths found from filesystem scan
        """
        executables = []
        build_dir = self.path_manager.build_dir

        # Common executable patterns to look for
        patterns = ['*_cli', '*_app', '*_test', '*_main', '*_demo', '*_example']

        for pattern in patterns:
            for exe_file in build_dir.rglob(pattern):
                # Skip CMake temporary files and directories
                if 'CMakeFiles' in str(exe_file):
                    continue

                # Skip if it's a directory
                if not exe_file.is_file():
                    continue

                # Check if it's executable
                if not os.access(exe_file, os.X_OK):
                    continue

                # Skip common non-executable files
                if exe_file.suffix in ['.txt', '.cmake', '.log', '.json', '.xml']:
                    continue

                executables.append(exe_file)

        # If no pattern-based executables found, do a broader search
        if not executables:
            for exe_file in build_dir.rglob('*'):
                # Skip CMake temporary files and directories
                if 'CMakeFiles' in str(exe_file):
                    continue

                # Skip if it's a directory
                if not exe_file.is_file():
                    continue

                # Check if it's executable
                if not os.access(exe_file, os.X_OK):
                    continue

                # Skip files with common non-executable extensions
                if exe_file.suffix in ['.txt', '.cmake', '.log', '.json', '.xml',
                                     '.a', '.so', '.dylib', '.o', '.obj', '.gcno',
                                     '.gcda', '.profraw', '.profdata']:
                    continue

                # Skip files that are clearly not executables
                if exe_file.name in ['Makefile', 'cmake_install.cmake']:
                    continue

                executables.append(exe_file)

        return executables

    def clean(self) -> bool:
        """
        Clean all pydcov coverage data.

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Cleaning pydcov coverage data...")

        # Remove entire pydcov_dir
        self.path_manager.clean_pydcov_data()

        # Also remove configuration file
        if self.config.config_exists():
            if self.config.remove_config():
                self.logger.info("Configuration file removed")
            else:
                self.logger.warning("Failed to remove configuration file")

        self.logger.success("PyDCov coverage data cleaned")
        return True

    def status(self) -> dict:
        """
        Get current incremental coverage status.

        Returns:
            Dictionary with status information
        """
        # Get status from file manager
        file_status = self.file_manager.get_status()

        # Add additional information
        status = {
            'build_root': str(self.path_manager.build_root),
            'pydcov_dir': str(self.path_manager.pydcov_dir),
            'compiler': self.compiler_detector.detect_compiler(),
            'pydcov_dir_exists': file_status.get('pydcov_dir_exists', False),
            'add_subdirs_count': file_status.get('add_subdirs_count', 0),
            'profraw_count': file_status['profraw_count'],
            'gcda_count': file_status['gcda_count'],
            'accumulated_files': file_status['profraw_count'] + file_status['gcda_count'],
            'merged_data_exists': file_status.get('merged_profdata_exists', False) or file_status.get('merged_info_exists', False),
            'report_exists': file_status['report_exists']
        }

        # Add file paths if they exist
        pydcov_dir = self.path_manager.pydcov_dir
        compiler = status['compiler']

        if compiler == 'clang':
            merged_file = pydcov_dir / 'merged.profdata'
            if merged_file.exists():
                status['merged_file'] = str(merged_file)
        else:
            merged_file = pydcov_dir / 'merged.info'
            if merged_file.exists():
                status['merged_file'] = str(merged_file)

        # Check for final report
        report_dir = pydcov_dir / 'report'
        if report_dir.exists() and (report_dir / 'index.html').exists():
            status['report_path'] = str(report_dir / 'index.html')

        return status

    def full_workflow(self, test_command: str | List[str]) -> bool:
        """
        Run complete incremental coverage workflow: init, add, merge, report.

        Args:
            test_command: Test command to execute. Must be specified explicitly.
                         Examples:
                         - "python -m pytest tests/"
                         - ["python", "-m", "unittest", "discover"]
                         - "./run_tests.sh"

        Returns:
            True if successful, False otherwise
        """
        self.logger.step("Starting incremental coverage full workflow...")

        # Initialize
        if not self.init():
            return False

        # Add coverage data
        if not self.add(test_command):
            return False

        # Merge data
        if not self.merge():
            return False

        # Generate report
        if not self.report():
            return False

        self.logger.success("Incremental coverage workflow completed successfully")
        return True
