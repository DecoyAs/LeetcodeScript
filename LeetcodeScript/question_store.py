"""
Question persistence for LeetCode Auto-Solver.
Downloads ALL questions for a difficulty to JSON.
Supports cache-check, force re-download, and resume via serial numbers.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _questions_file(difficulty):
    return os.path.join(DATA_DIR, f"questions_{difficulty.lower()}.json")


def save_questions(problems, difficulty):
    """Save fetched problems to a JSON file with serial numbers."""
    _ensure_data_dir()
    for i, p in enumerate(problems, 1):
        p["sr_no"] = i

    path = _questions_file(difficulty)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2)
    print(f"  [✓] Saved {len(problems)} questions → {os.path.basename(path)}")
    return problems


def load_questions(difficulty):
    """Load cached questions from JSON. Returns None if file doesn't exist."""
    path = _questions_file(difficulty)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        problems = json.load(f)
    return problems


def get_or_fetch_questions(difficulty, fetch_fn, force=False):
    """
    Check for cached questions file. If exists and not forced, use cache.
    Otherwise download ALL questions for the difficulty.

    Args:
        difficulty: "EASY", "MEDIUM", or "HARD"
        fetch_fn: callable(difficulty) -> list of problem dicts
        force: if True, re-download even if cache exists

    Returns:
        list of problem dicts (each with 'sr_no' key)
    """
    cached = load_questions(difficulty)

    if cached and not force:
        print(f"\n  [✓] {len(cached)} {difficulty.lower()} questions already downloaded.")
        print(f"      Using cached file. (Use 'Force re-download' to refresh.)")
        return cached

    if force and cached:
        print(f"\n  Force re-download requested. Replacing {len(cached)} cached questions...")

    print(f"\n  Downloading ALL {difficulty.lower()} problems from LeetCode...")
    problems = fetch_fn(difficulty)
    return save_questions(problems, difficulty)


def display_question_list(problems, start_from=1, max_display=30):
    """Print the question list (truncated for readability)."""
    total = len(problems)
    print(f"\n  Total questions: {total}")
    print(f"  {'#':<4} {'Title':<55} {'Slug'}")
    print("  " + "-" * 80)

    # Show a window around start_from
    if total <= max_display:
        show = problems
    else:
        # Show first few, then around start_from, then last few
        start_idx = max(0, start_from - 3)
        end_idx = min(total, start_idx + max_display)
        show = problems[start_idx:end_idx]
        if start_idx > 0:
            print(f"  ... ({start_idx} questions above) ...")

    for p in show:
        sr = p["sr_no"]
        marker = " → " if sr == start_from else "   "
        print(f"  {marker}{sr:<4} {p['title'][:53]:<55} {p['titleSlug']}")

    remaining = total - (start_from - 1)
    if total > max_display:
        shown_end = show[-1]["sr_no"] if show else 0
        if shown_end < total:
            print(f"  ... ({total - shown_end} more questions below) ...")

    print(f"\n  Starting from #{start_from} ({remaining} questions to solve)\n")
