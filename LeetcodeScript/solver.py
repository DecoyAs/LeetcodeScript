"""
AI Solver module for LeetCode Auto-Solver.
Uses Ollama to generate solutions with a retry loop that feeds
error feedback back to the model until the local judge passes.

Solutions are saved to:
  - submitted/   → successfully passing solutions
  - failed/      → final failed attempt when all retries are exhausted
"""

import re
import os
import ollama
from judge import run_local_test

# ── Configuration ─────────────────────────────────────────────────────────────
MAX_RETRIES = 5

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMITTED_DIR = os.path.join(PROJECT_DIR, "submitted")
FAILED_DIR = os.path.join(PROJECT_DIR, "failed")


def _ensure_dirs():
    os.makedirs(SUBMITTED_DIR, exist_ok=True)
    os.makedirs(FAILED_DIR, exist_ok=True)


def _extract_code(response_text):
    """Extract Python code from an AI response (handles markdown fences)."""
    match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.replace('```python', '').replace('```', '').strip()


def _build_prompt(snippet, problem_html, error_feedback=None):
    """
    Build a strict, optimized prompt that produces clean, correct LeetCode solutions.
    """
    prompt = f"""You are an expert competitive programmer. Solve this LeetCode problem.

## STRICT RULES — FOLLOW EVERY SINGLE ONE:
1. Return ONLY the `class Solution:` definition. Nothing else.
2. Do NOT add any comments, docstrings, or explanations in the code.
3. Do NOT include any `if __name__` block, test cases, or print statements.
4. Do NOT include any import statements UNLESS absolutely required (e.g., `from collections import defaultdict`).
5. If you need imports, place them INSIDE the method or at the very top before the class.
6. Use the EXACT method signature from the template below. Do not rename or change it.
7. Write clean, optimal, Pythonic code. Prefer O(n) or O(n log n) over brute force.
8. Handle edge cases: empty inputs, single elements, negative numbers, etc.
9. Use Python 3 syntax only. No Python 2 constructs.
10. Do NOT use `typing` imports unless they are already in the template.

## Template (use this exact signature):
```python
{snippet}
```

## Problem Description:
{problem_html}
"""
    if error_feedback:
        prompt += f"""
## PREVIOUS ATTEMPT FAILED
The previous solution produced this error or wrong output:
```
{error_feedback}
```
Analyze what went wrong. Fix the logic and return ONLY the corrected `class Solution:` code.
Do NOT repeat the same mistake.
"""
    return prompt


def solve(problem_details, python_snippet, func_name, slug, model_name, max_retries=None):
    """
    Generate a solution using the AI model and verify it with the local judge.
    Retries up to max_retries times, feeding errors back to the model each time.

    Args:
        problem_details: dict with 'content' and 'exampleTestcases'
        python_snippet: the LeetCode code template for Python 3
        func_name: name of the Solution method to test
        slug: problem slug (for saving files)
        model_name: Ollama model to use (e.g. "deepseek-coder:6.7b")
        max_retries: max attempts (default: MAX_RETRIES)

    Returns:
        The passing solution code (str), or None if all attempts failed.
    """
    if max_retries is None:
        max_retries = MAX_RETRIES

    _ensure_dirs()
    error_feedback = None
    last_solution = None

    for attempt in range(1, max_retries + 1):
        print(f"\n    [Attempt {attempt}/{max_retries}] Generating solution with {model_name}...")

        prompt = _build_prompt(python_snippet, problem_details["content"], error_feedback)

        try:
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            print(f"    [!] Ollama error: {e}")
            error_feedback = f"Ollama call failed: {e}"
            continue

        solution = _extract_code(response["message"]["content"])
        last_solution = solution

        # Run local judge
        print("    Running local judge...")
        result = run_local_test(solution, problem_details["exampleTestcases"], func_name)

        if result["passed"]:
            print(f"    ✓ Local test PASSED on attempt {attempt}!")
            # Save to submitted/ folder
            submitted_file = os.path.join(SUBMITTED_DIR, f"{slug}.py")
            with open(submitted_file, "w", encoding="utf-8") as f:
                f.write(solution)
            return solution
        else:
            error_msg = result.get("error") or result.get("output") or "Unknown error"
            error_feedback = error_msg
            print(f"    ✗ FAILED: {error_msg[:200]}")

    # All retries exhausted — save final failed attempt
    print(f"    [!] All {max_retries} attempts exhausted for '{slug}'. Skipping.")
    if last_solution:
        failed_file = os.path.join(FAILED_DIR, f"{slug}.py")
        with open(failed_file, "w", encoding="utf-8") as f:
            f.write(f"# FAILED after {max_retries} attempts\n")
            f.write(f"# Last error: {error_feedback[:200] if error_feedback else 'Unknown'}\n\n")
            f.write(last_solution)
        print(f"    Saved failed solution → failed/{slug}.py")

    return None
