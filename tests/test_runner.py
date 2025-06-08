#!/usr/bin/env python3
"""
Test runner script for the Bitcoin arbitrage project.
"""
import subprocess
import sys
from pathlib import Path


def run_tests(args=None):
    """Run pytest with specified arguments"""
    cmd = ["uv", "run", "pytest"]

    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main test runner function"""
    if len(sys.argv) == 1:
        print("Bitcoin Arbitrage Test Runner")
        print("=" * 40)
        print()
        print("Available commands:")
        print("  python test_runner.py unit          # Run only unit tests")
        print("  python test_runner.py integration   " "# Run only integration tests")
        print(
            "  python test_runner.py slow          " "# Run slow tests (real API calls)"
        )
        print("  python test_runner.py coverage      # Run with coverage report")
        print("  python test_runner.py all           # Run all tests")
        print("  python test_runner.py -v            # Verbose output")
        print("  python test_runner.py --help        # Show pytest help")
        print()
        print("Examples:")
        print("  python test_runner.py unit -v")
        print("  python test_runner.py tests/unit/test_currency_converter.py")
        return 0

    command = sys.argv[1]
    extra_args = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "unit":
        args = ["-m", "unit"] + extra_args
    elif command == "integration":
        args = ["-m", "integration"] + extra_args
    elif command == "slow":
        args = ["-m", "slow"] + extra_args
    elif command == "coverage":
        args = ["--cov=src", "--cov-report=html", "--cov-report=term"] + extra_args
    elif command == "all":
        args = extra_args
    else:
        # Pass through any other arguments directly to pytest
        args = sys.argv[1:]

    return run_tests(args)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
