"""
LeetCode Auto-Solver — Main Entry Point

Pipeline:
  1. CLI menu → Ollama check, login, pick difficulty, model, start position
  2. Download ALL questions (or use cached file)
  3. Login to LeetCode via Selenium
  4. For each problem: AI solve (with retry) → local judge → submit
  5. Print summary
"""

import re
import time
from cli import show_menu
from leetcode_client import get_problems, get_problem_details
from question_store import get_or_fetch_questions, display_question_list
from solver import solve
from submitter import get_driver, submit_to_leetcode, login_to_leetcode


def main():
    # ── 1. CLI Menu ───────────────────────────────────────────
    config = show_menu()
    if config is None:
        return

    model = config["model"]
    difficulty = config["difficulty"]
    start_from = config["start_from"]
    force_download = config["force_download"]

    # ── 2. Download / Load Questions ──────────────────────────
    print("\n" + "=" * 60)
    print("  📥  Questions")
    print("=" * 60)

    problems = get_or_fetch_questions(difficulty, get_problems, force=force_download)

    if not problems:
        print("  [!] No problems found. Exiting.")
        return

    display_question_list(problems, start_from)

    if start_from > len(problems):
        print(f"  [!] Start position #{start_from} exceeds {len(problems)} questions. Exiting.")
        return

    # ── 3. Login ──────────────────────────────────────────────
    print("=" * 60)
    print("  🔐  Browser & Login")
    print("=" * 60)

    driver = None
    try:
        driver = get_driver()
    except Exception as e:
        print(f"  [!] Failed to launch Chrome: {e}")
        return

    if driver is None:
        print("  [!] Browser failed to start. Aborting.")
        return

    if not login_to_leetcode(driver):
        driver.quit()
        return

    # ── 4. Solve & Submit Loop ────────────────────────────────
    print("=" * 60)
    print("  🚀  Starting Auto-Solve")
    print(f"  Model: {model}")
    print("=" * 60)

    submitted = 0
    skipped = 0
    failed = 0
    total = len(problems) - (start_from - 1)

    try:
        for problem in problems[start_from - 1:]:
            sr = problem.get("sr_no", "?")
            slug = problem["titleSlug"]
            title = problem["title"]

            print(f"\n{'─' * 60}")
            print(f"  #{sr}/{len(problems)} | {title}")
            print(f"  https://leetcode.com/problems/{slug}/")
            print(f"{'─' * 60}")

            # Fetch problem details
            try:
                details = get_problem_details(slug)
            except Exception as e:
                print(f"  [!] Could not fetch details: {e}. Skipping.")
                skipped += 1
                continue

            # Find Python 3 snippet
            snippet = None
            for s in details.get("codeSnippets", []):
                if s["langSlug"] == "python3":
                    snippet = s["code"]
                    break

            if not snippet:
                print("  [!] No Python 3 template found. Skipping.")
                skipped += 1
                continue

            func_match = re.search(r"def\s+(\w+)\s*\(", snippet)
            if not func_match:
                print("  [!] Could not parse function name. Skipping.")
                skipped += 1
                continue
            func_name = func_match.group(1)

            # Solve with AI (model passed from CLI, retry loop in solver.py)
            solution = solve(details, snippet, func_name, slug, model)

            if solution is None:
                print(f"  [!] AI could not solve '{title}'. Saved to failed/")
                failed += 1
                continue

            # Submit to LeetCode
            print("  Submitting to LeetCode...")
            success = submit_to_leetcode(driver, slug, solution)

            if success:
                submitted += 1
                print(f"  ✓ SUBMITTED! ({submitted}/{total} done)")
                time.sleep(10)
            else:
                print(f"  ✗ Submission failed for '{title}'.")
                failed += 1

    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted by user (Ctrl+C).")
    finally:
        if driver:
            driver.quit()

    # ── 5. Summary ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📊  Session Summary")
    print("=" * 60)
    print(f"    Model     : {model}")
    print(f"    Submitted : {submitted}")
    print(f"    Failed    : {failed}")
    print(f"    Skipped   : {skipped}")
    print(f"    Total     : {total}")
    print("=" * 60)
    print(f"    ✓ Solutions:  submitted/")
    print(f"    ✗ Failed:     failed/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()