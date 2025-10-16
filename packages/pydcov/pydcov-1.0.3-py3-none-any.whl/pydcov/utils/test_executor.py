#!/usr/bin/env python3
"""
Generic test execution utility for coverage tools.

This module provides a framework-agnostic interface for executing tests
with coverage data collection. It supports various testing frameworks
including pytest, unittest, custom executables, and shell commands.
"""

import subprocess
import shlex
from typing import List, Dict, Any
from pathlib import Path

from pydcov.utils.logging_config import setup_logging


class TestExecutor:
    """
    Generic test executor that can run any test command or executable.
    
    This class abstracts test execution to support multiple testing frameworks
    and custom test commands while maintaining consistent coverage data collection.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the test executor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logging()
    
    def execute_test_command(
        self,
        test_command: str | List[str],
        env: Dict[str, str] | None = None,
        timeout: int = 600,
        cwd: str | Path | None = None
    ) -> bool:
        """
        Execute a generic test command with coverage data collection.

        Args:
            test_command: Test command to execute. Can be:
                         - String: "python -m pytest tests/"
                         - List: ["python", "-m", "pytest", "tests/"]
                         Must not be None or empty.
            env: Environment variables for the test execution
            timeout: Timeout in seconds (default: 10 minutes)
            cwd: Working directory for command execution

        Returns:
            True if tests executed successfully (regardless of test results),
            False if execution failed

        Raises:
            ValueError: If test_command is None or empty
        """
        # Validate test command
        if not test_command:
            raise ValueError("Test command cannot be None or empty. Please specify a test command.")

        # Convert string command to list if needed
        if isinstance(test_command, str):
            if not test_command.strip():
                raise ValueError("Test command cannot be empty. Please specify a test command.")
            cmd = shlex.split(test_command)
        else:
            if not test_command:
                raise ValueError("Test command list cannot be empty. Please specify a test command.")
            cmd = list(test_command)
        
        # Use current working directory as default
        working_dir = Path(cwd) if cwd else Path.cwd()
        
        try:
            self.logger.info(f"Executing test command: {' '.join(cmd)}")
            self.logger.debug(f"Working directory: {working_dir}")
            
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                env=env,
                timeout=timeout,
                capture_output=False  # Let output go to console
            )
            
            if result.returncode == 0:
                self.logger.success("Test command completed successfully")
                return True
            else:
                self.logger.warning(f"Test command completed with return code {result.returncode}")
                # Don't fail on test failures, we still want coverage data
                return True
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test command timed out after {timeout} seconds")
            return False
        except FileNotFoundError:
            self.logger.error(f"Test command not found: {cmd[0]}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to execute test command: {e}")
            return False
    
    @staticmethod
    def parse_test_command(command_args: List[str]) -> str | List[str]:
        """
        Parse test command arguments into a proper command.

        This method handles various input formats without making assumptions
        about specific testing frameworks.

        Args:
            command_args: List of command arguments (must not be empty)

        Returns:
            Parsed command as string or list

        Raises:
            ValueError: If command_args is empty or invalid
        """
        if not command_args:
            raise ValueError("Test command arguments cannot be empty. Please specify a test command.")

        # If it's a single string that looks like a complete command, return as-is
        if len(command_args) == 1 and (' ' in command_args[0]):
            return command_args[0]

        # If first argument looks like a test framework command, use as-is
        if command_args[0] in ['python', 'python3', 'pytest', 'unittest', 'nose2', 'green', 'tox', 'make']:
            return command_args

        # If first argument is a script or executable, use as-is
        if (command_args[0].startswith('./') or
            command_args[0].startswith('/') or
            command_args[0].endswith('.sh') or
            command_args[0].endswith('.py')):
            return command_args

        # Otherwise, treat as a complete command without assumptions
        return command_args
    
    @staticmethod
    def get_common_test_commands() -> Dict[str, List[str]]:
        """
        Get common test command templates for different frameworks.
        
        Returns:
            Dictionary mapping framework names to command templates
        """
        return {
            'pytest': ["python3", "-m", "pytest"],
            'unittest': ["python3", "-m", "unittest"],
            'nose2': ["python3", "-m", "nose2"],
            'green': ["green"],
            'tox': ["tox"],
            'make_test': ["make", "test"],
            'npm_test': ["npm", "test"],
            'cargo_test': ["cargo", "test"],
            'go_test': ["go", "test"],
            'custom': []  # User-defined command
        }
    
    def validate_test_command(self, test_command: str | List[str]) -> bool:
        """
        Validate that a test command is executable.
        
        Args:
            test_command: Test command to validate
            
        Returns:
            True if command appears to be valid, False otherwise
        """
        if isinstance(test_command, str):
            cmd = shlex.split(test_command)
        else:
            cmd = list(test_command)
        
        if not cmd:
            return False
        
        # Check if the first command exists
        try:
            result = subprocess.run(
                [cmd[0], '--help'],
                capture_output=True,
                timeout=5
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Try with 'which' or 'where' command
            try:
                which_cmd = 'where' if subprocess.run(['where', '/q', 'cmd'], capture_output=True).returncode == 0 else 'which'
                result = subprocess.run([which_cmd, cmd[0]], capture_output=True)
                return result.returncode == 0
            except:
                return False
