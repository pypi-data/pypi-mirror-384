"""
Comprehensive test runner for the data_exchange_agent package.

This script runs all tests and provides a summary of test results.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def discover_and_run_tests():
    """Discover and run all tests in the tests directory."""
    tests_dir = Path(__file__).parent

    loader = unittest.TestLoader()

    test_suite = loader.discover(
        start_dir=str(tests_dir), pattern="test_*.py", top_level_dir=str(project_root)
    )

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=True)

    result = runner.run(test_suite)

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")

    if result.skipped:
        print(f"\nSKIPPED ({len(result.skipped)}):")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")

    return result.wasSuccessful()


def list_test_files():
    """List all test files that will be run."""
    tests_dir = Path(__file__).parent
    test_files = list(tests_dir.glob("test_*.py"))
    test_files.sort()

    print("Test files to be executed:")
    print("-" * 40)
    for test_file in test_files:
        print(f"  {test_file.name}")
    print(f"\nTotal: {len(test_files)} test files")
    print()


if __name__ == "__main__":
    print("Data Exchange Agent - Comprehensive Test Suite")
    print("=" * 50)
    print()

    list_test_files()

    success = discover_and_run_tests()

    sys.exit(0 if success else 1)
