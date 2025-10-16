#!/usr/bin/env python3
"""
PyDCov Command Line Interface

Streamlined command-line interface for PyDCov incremental coverage tracking
and CMake integration for C/C++ projects.

Usage:
    pydcov [command] [options]
    pydcov --help
    pydcov --version

Commands:
    init          - Initialize incremental coverage tracking (requires --build-root)
    add           - Add coverage data from test run (creates unique subdirectory)
    merge         - Merge coverage data from all test runs
    report        - Generate comprehensive coverage report
    status        - Show coverage status and directory information
    clean         - Clean all coverage data and configuration
    export        - Export coverage data to standard formats (lcov, json)
    init-cmake    - Initialize CMake integration

Examples:
    # Initialize with build directory (only required once)
    pydcov init --build-root build

    # Initialize with custom pydcov directory location
    pydcov init --build-root build --pydcov-dir /path/to/coverage/data

    # All subsequent commands use stored configuration
    pydcov add python -m pytest tests/ -v --tb=short
    pydcov add python -m unittest discover tests/
    pydcov add ./run_tests.sh
    pydcov add --timeout 1200 python -m pytest tests/slow/  # Custom timeout
    pydcov merge
    pydcov report
    pydcov status
    pydcov clean
    pydcov export --format lcov
    pydcov export --format json --output coverage.json

    # CMake integration (independent of build root)
    pydcov init-cmake
"""

import argparse
import sys
from pathlib import Path
# No typing imports needed for Python 3.11+ union syntax

from pydcov import __version__
from pydcov.core.incremental_coverage import IncrementalCoverageManager
from pydcov.utils.logging_config import setup_logging


def add_common_arguments(parser):
    """Add common arguments to a parser."""
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--no-colors',
        action='store_true',
        help='Disable colored output'
    )


def add_init_arguments(parser):
    """Add arguments specific to the init command."""
    parser.add_argument(
        '--build-root',
        type=Path,
        help='CMake build directory (auto-detected if not specified)'
    )
    parser.add_argument(
        '--pydcov-dir',
        type=Path,
        help='Directory for pydcov coverage data (default: current working directory)'
    )


def create_init_cmake_parser(subparsers):
    """Create init-cmake command parser."""
    init_parser = subparsers.add_parser(
        'init-cmake',
        help='Initialize CMake integration',
        description='Copy CMake integration files to your project'
    )

    init_parser.add_argument(
        '--project-root',
        type=str,
        help='Project root directory (current directory if not specified)'
    )

    init_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing files'
    )

    return init_parser


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='pydcov',
        description='PyDCov - Incremental C/C++ Code Coverage Tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'PyDCov {__version__}'
    )

    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='Available commands',
        metavar='COMMAND'
    )

    # Create incremental coverage commands
    init_parser = subparsers.add_parser('init',
                                       help='Initialize incremental coverage tracking',
                                       description='Initialize incremental coverage tracking and save build root and coverage directory configuration for subsequent commands')
    add_common_arguments(init_parser)
    add_init_arguments(init_parser)

    add_parser = subparsers.add_parser('add',
                                      help='Add coverage data from test run',
                                      description='Run tests and add coverage data to incremental collection')
    add_parser.add_argument('test_args', nargs=argparse.REMAINDER,
                           help='Complete test command with all arguments (e.g., python -m pytest tests/ -v)')
    add_parser.add_argument('--timeout', type=int, default=None,
                           help='Timeout in seconds for test execution (default: 600)')
    add_common_arguments(add_parser)

    merge_parser = subparsers.add_parser('merge',
                                        help='Merge coverage data',
                                        description='Merge coverage data')
    add_common_arguments(merge_parser)

    report_parser = subparsers.add_parser('report',
                                         help='Generate incremental coverage report',
                                         description='Generate incremental coverage report (automatically merges data if needed)')
    add_common_arguments(report_parser)

    status_parser = subparsers.add_parser('status',
                                         help='Show incremental coverage status',
                                         description='Show incremental coverage status')
    add_common_arguments(status_parser)

    clean_parser = subparsers.add_parser('clean',
                                        help='Clean incremental coverage data',
                                        description='Clean incremental coverage data')
    add_common_arguments(clean_parser)

    export_parser = subparsers.add_parser('export',
                                         help='Export coverage data to standard formats',
                                         description='Export coverage data to formats like lcov, json for external tools')
    export_parser.add_argument('--format', '-f',
                              choices=['lcov', 'json', 'cobertura'],
                              default='lcov',
                              help='Export format (default: lcov)')
    export_parser.add_argument('--output', '-o',
                              type=Path,
                              help='Output file path (optional, uses default if not specified)')
    add_common_arguments(export_parser)

    # Create init-cmake command
    create_init_cmake_parser(subparsers)

    return parser.parse_args()


def handle_incremental_command(args) -> int:
    """Handle incremental coverage command."""
    try:
        is_init_command = args.subcommand == 'init'
        build_root = getattr(args, 'build_root', None)
        pydcov_dir = getattr(args, 'pydcov_dir', None)
        manager = IncrementalCoverageManager(build_root=build_root, pydcov_dir=pydcov_dir, is_init_command=is_init_command)

        if args.subcommand == 'init':
            success = manager.init()
        elif args.subcommand == 'add':
            if not args.test_args:
                print("Error: add command requires test arguments")
                return 1
            success = manager.add(args.test_args, timeout=args.timeout)
        elif args.subcommand == 'merge':
            success = manager.merge()
        elif args.subcommand == 'report':
            success = manager.report()
        elif args.subcommand == 'status':
            success = manager.status()
        elif args.subcommand == 'clean':
            success = manager.clean()
        elif args.subcommand == 'export':
            success = manager.file_manager.export_coverage_data(args.format, args.output)
        else:
            print(f"Error: Unknown command: {args.subcommand}")
            return 1

        return 0 if success else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def copy_cmake_files_from_traversable_with_force(cmake_traversable, cmake_dir: Path, force: bool):
    """Copy CMake files from importlib.resources.Traversable with force option."""
    import shutil

    for item in cmake_traversable.iterdir():
        if item.is_file() and item.name.endswith('.cmake'):
            dest_file = cmake_dir / item.name

            if dest_file.exists() and not force:
                print(f"File {dest_file} already exists. Use --force to overwrite.")
                continue

            with item.open('rb') as src, open(dest_file, 'wb') as dst:
                shutil.copyfileobj(src, dst)
            print(f"Copied {item.name} to {dest_file}")


def handle_init_cmake_command(args) -> int:
    """Handle init-cmake command."""
    try:
        import shutil
        import importlib.resources

        # Handle project root with robust path resolution
        if args.project_root is not None:
            project_root = Path(args.project_root)
        else:
            try:
                project_root = Path.cwd()
            except (OSError, RuntimeError) as e:
                print(f"Error: Cannot determine current working directory: {e}")
                return 1

        # Ensure project_root is a valid Path object
        if not isinstance(project_root, Path):
            try:
                project_root = Path(project_root)
            except (TypeError, ValueError) as e:
                print(f"Error: Invalid project root: {e}")
                return 1

        cmake_dir = project_root / "cmake"

        # Create cmake directory if it doesn't exist
        cmake_dir.mkdir(exist_ok=True)

        # Copy CMake files from package
        try:
            # Try new importlib.resources API (Python 3.9+)
            cmake_files = importlib.resources.files('pydcov.cmake')
            copy_cmake_files_from_traversable_with_force(cmake_files, cmake_dir, getattr(args, 'force', False))

        except (ImportError, AttributeError):
            # Fallback for older Python versions
            import pkg_resources
            package_cmake_dir = Path(pkg_resources.resource_filename('pydcov', 'cmake'))

            for cmake_file in package_cmake_dir.glob('*.cmake'):
                dest_file = cmake_dir / cmake_file.name

                if dest_file.exists() and not getattr(args, 'force', False):
                    print(f"File {dest_file} already exists. Use --force to overwrite.")
                    continue

                shutil.copy2(cmake_file, dest_file)
                print(f"Copied {cmake_file.name} to {dest_file}")

        print(f"\nCMake integration files copied to {cmake_dir}")
        print("Add the following line to your CMakeLists.txt:")
        print("    include(cmake/coverage.cmake)")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    level = "DEBUG" if getattr(args, 'verbose', False) else "INFO"
    setup_logging(
        level=level,
        use_colors=not getattr(args, 'no_colors', False)
    )

    if not args.subcommand:
        print("Error: No command specified. Use 'pydcov --help' for usage information.")
        return 1

    if args.subcommand == 'init-cmake':
        return handle_init_cmake_command(args)
    elif args.subcommand in ['init', 'add', 'merge', 'report', 'status', 'clean', 'export']:
        return handle_incremental_command(args)
    else:
        print(f"Error: Unknown command: {args.subcommand}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
