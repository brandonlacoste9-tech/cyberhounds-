#!/usr/bin/env python3
"""
🧪 CYBERHOUND TEST RUNNER
Comprehensive test execution with coverage reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run the test suite."""
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=hound_core", "--cov-report=term-missing", "--cov-report=html"])
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "swarm":
        cmd.append("tests/test_swarm.py")
    elif test_type == "sovereign":
        cmd.append("tests/test_sovereign.py")
    else:
        cmd.append("tests/")
    
    print("🧪 Running Cyberhound tests...")
    print(f"   Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="🧪 Cyberhound Test Runner")
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "swarm", "sovereign"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    return run_tests(args.type, args.verbose, args.coverage)


if __name__ == "__main__":
    sys.exit(main())
