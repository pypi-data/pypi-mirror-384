#!/usr/bin/env python3
"""Test runner script for mixtrain tests."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Main test runner."""
    # Change to the mixtrain directory
    mixtrain_dir = Path(__file__).parent
    original_dir = Path.cwd()
    
    try:
        import os
        os.chdir(mixtrain_dir)
        
        print("🧪 Mixtrain Test Suite Runner")
        print(f"📁 Working directory: {mixtrain_dir}")
        
        # Check if we're in a virtual environment or have uv
        has_uv = subprocess.run(["which", "uv"], capture_output=True).returncode == 0
        
        if has_uv:
            python_cmd = ["uv", "run", "python"]
            pytest_cmd = ["uv", "run", "pytest"]
        else:
            python_cmd = ["python"]
            pytest_cmd = ["pytest"]
        
        success_count = 0
        total_tests = 0
        
        # Test categories to run
        test_categories = [
            (pytest_cmd + ["tests/test_config.py", "-v"], "Configuration Tests"),
            (pytest_cmd + ["tests/test_client.py", "-v"], "SDK Client Tests"),
            (pytest_cmd + ["tests/test_dataset.py", "-v"], "Dataset Module Tests"),
            (pytest_cmd + ["tests/test_provider.py", "-v"], "Provider Module Tests"),
            (pytest_cmd + ["tests/test_secret.py", "-v"], "Secret Module Tests"),
            (pytest_cmd + ["tests/test_cli.py", "-v"], "CLI Command Tests"),
            (pytest_cmd + ["tests/test_integration.py", "-v"], "Integration Tests"),
        ]
        
        # Run all test categories
        for cmd, description in test_categories:
            total_tests += 1
            if run_command(cmd, description):
                success_count += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🏁 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {success_count}/{total_tests}")
        print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 All tests passed!")
            return 0
        else:
            print("💥 Some tests failed!")
            return 1
            
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    sys.exit(main())

