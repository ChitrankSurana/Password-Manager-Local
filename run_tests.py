#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Runner for Personal Password Manager
========================================

Comprehensive test runner that executes all test suites and provides
detailed reporting on test results, coverage, and performance.

Usage:
    python run_tests.py [options]

Options:
    --unit          Run only unit tests
    --integration   Run only integration tests
    --security      Run only security tests
    --coverage      Run tests with coverage reporting
    --verbose       Verbose output
    --fast          Skip slow tests
"""

import argparse
import os
import sys
import time
import unittest
from io import StringIO
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "tests"))

# Test imports
try:
    import test_password_manager
    import test_web_interface
except ImportError as e:
    print(f"Error importing test modules: {e}")
    sys.exit(1)

# Optional coverage import
try:
    import coverage

    HAS_COVERAGE = True
except ImportError:
    HAS_COVERAGE = False
    print("Coverage not available. Install with: pip install coverage")


class TestResult:
    """Container for test results"""

    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.execution_time = 0
        self.failures = []
        self.errors = []


class ColoredTextTestRunner(unittest.TextTestRunner):
    """Test runner with colored output"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = self._supports_color()

    def _supports_color(self):
        """Check if terminal supports colors"""
        try:
            import colorama

            colorama.init()
            return True
        except ImportError:
            return os.getenv("TERM") and "color" in os.getenv("TERM", "")

    def _colorize(self, text, color):
        """Colorize text if supported"""
        if not self.use_colors:
            return text

        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }

        return f"{colors.get(color, '')}{text}{colors['reset']}"

    def run(self, test):
        """Run tests with colored output"""
        result = super().run(test)

        # Print colored summary
        if result.wasSuccessful():
            print(self._colorize("\n✓ ALL TESTS PASSED", "green"))
        else:
            print(self._colorize("\n✗ SOME TESTS FAILED", "red"))

        return result


def run_test_suite(test_suite, verbose=False):
    """Run a test suite and return results"""
    start_time = time.time()

    # Capture output
    stream = StringIO()
    runner = ColoredTextTestRunner(
        stream=stream if not verbose else sys.stdout, verbosity=2 if verbose else 1
    )

    result = runner.run(test_suite)
    end_time = time.time()

    # Create result object
    test_result = TestResult()
    test_result.total_tests = result.testsRun
    test_result.passed_tests = result.testsRun - len(result.failures) - len(result.errors)
    test_result.failed_tests = len(result.failures)
    test_result.error_tests = len(result.errors)
    test_result.execution_time = end_time - start_time
    test_result.failures = result.failures
    test_result.errors = result.errors

    if not verbose:
        print(stream.getvalue())

    return test_result


def run_unit_tests(verbose=False):
    """Run unit tests"""
    print("\n" + "=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestSuite()

    # Add unit tests
    suite.addTest(unittest.makeSuite(test_password_manager.TestPasswordManager))
    suite.addTest(unittest.makeSuite(test_password_manager.TestPasswordEncryption))
    suite.addTest(unittest.makeSuite(test_password_manager.TestErrorHandling))

    return run_test_suite(suite, verbose)


def run_integration_tests(verbose=False):
    """Run integration tests"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test_web_interface.TestWebInterface))

    return run_test_suite(suite, verbose)


def run_security_tests(verbose=False):
    """Run security tests"""
    print("\n" + "=" * 60)
    print("RUNNING SECURITY TESTS")
    print("=" * 60)

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(test_web_interface.TestWebSecurity))

    return run_test_suite(suite, verbose)


def run_all_tests(verbose=False, with_coverage=False):
    """Run all tests"""
    results = []

    # Start coverage if requested
    cov = None
    if with_coverage and HAS_COVERAGE:
        cov = coverage.Coverage()
        cov.start()
        print("Coverage tracking enabled")

    try:
        # Run test suites
        results.append(("Unit Tests", run_unit_tests(verbose)))
        results.append(("Integration Tests", run_integration_tests(verbose)))
        results.append(("Security Tests", run_security_tests(verbose)))

    finally:
        # Stop coverage
        if cov:
            cov.stop()
            cov.save()

    # Print summary
    print_test_summary(results)

    # Generate coverage report
    if cov:
        print("\n" + "=" * 60)
        print("COVERAGE REPORT")
        print("=" * 60)

        cov.report(show_missing=True)

        # Generate HTML report
        html_dir = Path("htmlcov")
        cov.html_report(directory=str(html_dir))
        print(f"\nHTML coverage report generated in: {html_dir}")

    # Return overall success
    return all(result.failed_tests == 0 and result.error_tests == 0 for _, result in results)


def print_test_summary(results):
    """Print test execution summary"""
    print("\n" + "=" * 60)
    print("TEST EXECUTION SUMMARY")
    print("=" * 60)

    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_time = 0

    for test_type, result in results:
        print(f"\n{test_type}:")
        print(f"  Tests run: {result.total_tests}")
        print(f"  Passed: {result.passed_tests}")
        print(f"  Failed: {result.failed_tests}")
        print(f"  Errors: {result.error_tests}")
        print(f"  Time: {result.execution_time:.2f}s")

        total_tests += result.total_tests
        total_passed += result.passed_tests
        total_failed += result.failed_tests
        total_errors += result.error_tests
        total_time += result.execution_time

    print("\nOVERALL:")
    print(f"  Total tests: {total_tests}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_failed}")
    print(f"  Errors: {total_errors}")
    print(f"  Success rate: {(total_passed / total_tests * 100):.1f}%")
    print(f"  Total time: {total_time:.2f}s")

    # Print failure details
    if total_failed > 0 or total_errors > 0:
        print("\nFAILURES AND ERRORS:")
        print("-" * 40)

        for test_type, result in results:
            if result.failures:
                print(f"\n{test_type} Failures:")
                for test, traceback in result.failures:
                    print(f"  - {test}")
                    if len(traceback) < 500:  # Only show short tracebacks
                        print(f"    {traceback}")

            if result.errors:
                print(f"\n{test_type} Errors:")
                for test, traceback in result.errors:
                    print(f"  - {test}")
                    if len(traceback) < 500:
                        print(f"    {traceback}")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run tests for Personal Password Manager")

    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--security", action="store_true", help="Run only security tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")

    args = parser.parse_args()

    print("Personal Password Manager - Test Runner")
    print("=======================================")

    # Check dependencies
    print("Checking test dependencies...")

    # Run specific test suites
    success = True

    if args.unit:
        result = run_unit_tests(args.verbose)
        success = result.failed_tests == 0 and result.error_tests == 0

    elif args.integration:
        result = run_integration_tests(args.verbose)
        success = result.failed_tests == 0 and result.error_tests == 0

    elif args.security:
        result = run_security_tests(args.verbose)
        success = result.failed_tests == 0 and result.error_tests == 0

    else:
        # Run all tests
        success = run_all_tests(args.verbose, args.coverage)

    # Exit with appropriate code
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
