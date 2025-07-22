#!/usr/bin/env python3
"""
Main test runner for all tool_calls tests
"""

import os
import subprocess
import sys


def run_test_script(script_path):
    """Run a test script and return success status"""
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(script_path),
        )
        if result.returncode == 0:
            print(f"✅ {os.path.basename(script_path)} - PASSED")
            print(result.stdout)
            return True
        else:
            print(f"❌ {os.path.basename(script_path)} - FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ {os.path.basename(script_path)} - ERROR: {e}")
        return False


def main():
    """Run all test scripts"""
    print("🚀 Running all tool_calls tests...\n")

    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_scripts = [
        os.path.join(test_dir, "test_toolcall.py"),
        os.path.join(test_dir, "test_tool.py"),
        os.path.join(test_dir, "test_toolchoice.py"),
    ]

    passed = 0
    total = len(test_scripts)

    for script in test_scripts:
        if os.path.exists(script):
            if run_test_script(script):
                passed += 1
            print("-" * 60)
        else:
            print(f"❌ Test script not found: {script}")

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
