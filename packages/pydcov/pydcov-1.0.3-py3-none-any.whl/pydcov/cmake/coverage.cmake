# ==============================================================================
# Build-Only Coverage Configuration Module for CMake
# ==============================================================================
# This module provides build configuration for C/C++ code coverage.
# Coverage file operations have been moved to PyDCov's pure Python implementation.
#
# COVERAGE OPERATIONS:
#   Use PyDCov commands instead of CMake targets:
#   - pydcov coverage clean    (replaces make coverage-clean)
#   - pydcov coverage report   (replaces make coverage-report)
#   - pydcov coverage full "test_cmd"  (complete workflow)
#
# This module now only handles:
# - Compiler flag configuration for coverage instrumentation
# - Coverage library linking
# - Executable registration (for compatibility)
# - Build environment setup
#
# Features:
# - Cross-platform support (Linux, macOS, Windows)
# - Automatic compiler detection and flag configuration
# - Support for both GCC/gcov and Clang/llvm-cov toolchains
# - Executable registration for compatibility with legacy code
# - Generic and reusable across different project structures
#
# Usage:
#   include(cmake/coverage.cmake)
#   # Optional executable registration (for compatibility):
#   coverage_add_executable(my_executable)
#   # Build with coverage: PYDCOV_ENABLE_COVERAGE=1 cmake ..
#   # Generate reports: pydcov coverage report
# ==============================================================================

# Check for coverage environment variable
if(NOT ENV{PYDCOV_ENABLE_COVERAGE} STREQUAL "")
    message(STATUS "PYDCOV_ENABLE_COVERAGE was set, value = ${PYDCOV_ENABLE_COVERAGE}")
    string(TOUPPER "$ENV{PYDCOV_ENABLE_COVERAGE}" COVERAGE_ENV_VALUE)

    # Set a cache variable to mark that coverage is enabled
    # This provides a reliable marker for PyDCov to detect coverage builds
    set(PYDCOV_COVERAGE_ENABLED ON CACHE BOOL "PyDCov coverage instrumentation is enabled")
else()
    # Only proceed if coverage is enabled
    message(ERROR "Note: PYDCOV_ENABLE_COVERAGE was not set as environment variable.")
    return()
endif()

# ==============================================================================
# Coverage Executable Registration Functions
# ==============================================================================

# Function to register an executable for coverage analysis (compatibility only)
function(coverage_add_executable target_name)
    if(NOT TARGET ${target_name})
        message(WARNING "coverage_add_executable: Target '${target_name}' does not exist")
        return()
    endif()

    get_target_property(target_type ${target_name} TYPE)
    if(NOT target_type STREQUAL "EXECUTABLE")
        message(WARNING "coverage_add_executable: Target '${target_name}' is not an executable")
        return()
    endif()

    message(STATUS "Registered executable for coverage: ${target_name}")
endfunction()

message(STATUS "Coverage enabled - configuring coverage tools...")

# ==============================================================================
# Compiler Detection and Flag Configuration
# ==============================================================================

if(CMAKE_C_COMPILER_ID MATCHES "GNU")
    set(COVERAGE_FLAGS "--coverage -fprofile-arcs -ftest-coverage")
    set(COVERAGE_LIBS "gcov")
    message(STATUS "Using GCC coverage with gcov")
elseif(CMAKE_C_COMPILER_ID MATCHES "Clang")
    set(COVERAGE_FLAGS "-fprofile-instr-generate -fcoverage-mapping")
    set(COVERAGE_LIBS "")
    message(STATUS "Using Clang coverage with llvm-cov")
else()
    message(WARNING "Coverage requested but compiler ${CMAKE_C_COMPILER_ID} is not supported")
    message(WARNING "Supported compilers: GCC, Clang")
    return()
endif()

# Apply coverage flags to compiler and linker
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COVERAGE_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COVERAGE_FLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${COVERAGE_FLAGS}")

# ==============================================================================
# Coverage Library Linking Function
# ==============================================================================

function(target_link_coverage_libraries target_name)
    if(COVERAGE_LIBS)
        target_link_libraries(${target_name} PRIVATE ${COVERAGE_LIBS})
        message(STATUS "Linked coverage libraries to ${target_name}: ${COVERAGE_LIBS}")
    endif()

    # Auto-register executable for coverage if it's an executable (compatibility)
    if(TARGET ${target_name})
        get_target_property(target_type ${target_name} TYPE)
        if(target_type STREQUAL "EXECUTABLE")
            coverage_add_executable(${target_name})
        endif()
    endif()
endfunction()

# ==============================================================================
# Coverage Directory Setup
# ==============================================================================

# Create coverage output directory
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/coverage)

# ==============================================================================
# Coverage Tool Detection
# ==============================================================================

if(CMAKE_C_COMPILER_ID MATCHES "Clang")
    # Find LLVM tools (they might be versioned on Ubuntu, or accessed via xcrun on macOS)
    if(APPLE)
        # On macOS, try xcrun first
        find_program(XCRUN_EXECUTABLE xcrun)
        if(XCRUN_EXECUTABLE)
            execute_process(COMMAND ${XCRUN_EXECUTABLE} --find llvm-profdata
                          OUTPUT_VARIABLE LLVM_PROFDATA_EXECUTABLE
                          OUTPUT_STRIP_TRAILING_WHITESPACE
                          ERROR_QUIET)
            execute_process(COMMAND ${XCRUN_EXECUTABLE} --find llvm-cov
                          OUTPUT_VARIABLE LLVM_COV_EXECUTABLE
                          OUTPUT_STRIP_TRAILING_WHITESPACE
                          ERROR_QUIET)
        endif()
    endif()

    # If not found via xcrun or not on macOS, try standard search
    if(NOT LLVM_PROFDATA_EXECUTABLE)
        find_program(LLVM_PROFDATA_EXECUTABLE NAMES llvm-profdata llvm-profdata-18 llvm-profdata-17 llvm-profdata-16 llvm-profdata-15 llvm-profdata-14)
    endif()
    if(NOT LLVM_COV_EXECUTABLE)
        find_program(LLVM_COV_EXECUTABLE NAMES llvm-cov llvm-cov-18 llvm-cov-17 llvm-cov-16 llvm-cov-15 llvm-cov-14)
    endif()

    if(NOT LLVM_PROFDATA_EXECUTABLE)
        message(FATAL_ERROR "llvm-profdata not found. Please install LLVM tools.")
    endif()

    if(NOT LLVM_COV_EXECUTABLE)
        message(FATAL_ERROR "llvm-cov not found. Please install LLVM tools.")
    endif()

    message(STATUS "Found llvm-profdata: ${LLVM_PROFDATA_EXECUTABLE}")
    message(STATUS "Found llvm-cov: ${LLVM_COV_EXECUTABLE}")
endif()

# ==============================================================================
# Coverage Status Summary
# ==============================================================================

message(STATUS "Coverage configuration complete:")
message(STATUS "  Coverage Flags: ${COVERAGE_FLAGS}")
if(COVERAGE_LIBS)
    message(STATUS "  Coverage Libraries: ${COVERAGE_LIBS}")
endif()

