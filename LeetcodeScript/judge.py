"""
Local judge for LeetCode Auto-Solver.
Runs the AI-generated solution against example test cases locally
and returns structured pass/fail results.
"""

import subprocess
import sys
import os
import ast
import tempfile


def run_local_test(code, test_cases, func_name):
    """
    Run the solution locally against LeetCode example test cases.

    Args:
        code: the Python solution code (must contain class Solution)
        test_cases: newline-separated test case inputs from LeetCode
        func_name: name of the Solution method to call

    Returns:
        dict with keys:
            passed (bool): True if code ran without errors
            output (str): stdout from the test run
            error  (str): stderr from the test run (empty if passed)
    """
    # Parse test case inputs
    try:
        parsed_input = [
            ast.literal_eval(line.strip())
            for line in test_cases.split('\n')
            if line.strip()
        ]
    except Exception:
        parsed_input = test_cases.split('\n')

    # Build test harness
    harness = f"""import inspect
from typing import *

{code}

if __name__ == "__main__":
    sol = Solution()
    try:
        sig = inspect.signature(sol.{func_name})
        num_args = len([p for p in sig.parameters.values() if p.name != 'self'])
        p_input = {repr(parsed_input)}
        result = sol.{func_name}(*p_input[:num_args])
        print(result)
    except Exception as e:
        print(f"Error: {{e}}", file=__import__('sys').stderr)
"""

    # Write to a temp file (cross-platform)
    tmp_dir = tempfile.gettempdir()
    tmp_file = os.path.join(tmp_dir, "leetcode_test_harness.py")

    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(harness)

        res = subprocess.run(
            [sys.executable, tmp_file],
            capture_output=True,
            text=True,
            timeout=30,
        )

        stdout = res.stdout.strip()
        stderr = res.stderr.strip()

        if res.returncode == 0 and not stderr:
            return {"passed": True, "output": stdout, "error": ""}
        else:
            return {"passed": False, "output": stdout, "error": stderr or f"Exit code: {res.returncode}"}

    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "", "error": "Execution timed out (30s limit)"}
    except Exception as e:
        return {"passed": False, "output": "", "error": str(e)}
    finally:
        # Clean up
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass
