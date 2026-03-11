"""
Interactive CLI menu for LeetCode Auto-Solver.
Handles login credentials, Ollama model selection, difficulty, download mode, and resume.
"""

import getpass
import os
import shutil
import subprocess
import sys


def _check_ollama_installed():
    """Check if Ollama is installed and accessible."""
    if shutil.which("ollama") is not None:
        return True

    # Try running ollama directly in case it's not on PATH but installed
    try:
        subprocess.run(
            ["ollama", "--version"],
            capture_output=True, timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _get_available_models():
    """Get list of locally available Ollama models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []

        models = []
        for line in result.stdout.strip().split("\n")[1:]:  # Skip header
            if line.strip():
                model_name = line.split()[0]
                models.append(model_name)
        return models
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _check_ollama_ready():
    """
    Verify Ollama is installed and has at least one model.
    Guides the user through setup if not ready.

    Returns:
        str: selected model name, or None if user aborts.
    """
    print("\n" + "=" * 60)
    print("  🤖  Ollama Setup Check")
    print("=" * 60)

    # 1. Check Ollama installed
    if not _check_ollama_installed():
        print("\n  [!] Ollama is NOT installed on this system.")
        print("      Ollama is required to run AI code generation.\n")
        print("  Install it from: https://ollama.com/download")
        print("  After installing, restart your terminal and run this again.\n")
        input("  Press ENTER to exit...")
        return None

    print("  [✓] Ollama is installed.")

    # 2. Check for available models
    models = _get_available_models()

    if not models:
        print("\n  [!] No Ollama models found locally.")
        print("      You need to pull a model first.\n")
        print("  Recommended models:")
        print("    ollama pull deepseek-coder:6.7b    (best quality, needs ~4GB RAM)")
        print("    ollama pull deepseek-coder:1.3b    (faster, needs ~1GB RAM)")
        print("    ollama pull codellama:7b            (alternative)")
        print("    ollama pull qwen2.5-coder:7b        (alternative)\n")
        print("  Run one of the commands above, then restart this script.")
        input("\n  Press ENTER to exit...")
        return None

    # 3. Let user pick a model
    print(f"  [✓] Found {len(models)} model(s) available:\n")
    for i, model in enumerate(models, 1):
        print(f"    [{i}] {model}")

    while True:
        raw = input(f"\n  Select model (1-{len(models)}): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(models):
            selected = models[int(raw) - 1]
            print(f"  [✓] Using model: {selected}")
            return selected
        print("  ✗ Invalid choice.")


def ask_credentials():
    """
    Ask the user for LeetCode credentials via CLI.
    Sets them as environment variables for the current session.

    Returns:
        tuple: (username, password) or (None, None) on failure.
    """
    print("\n" + "=" * 60)
    print("  🔐  LeetCode Login")
    print("=" * 60)

    username = input("  Username / Email : ").strip()
    password = getpass.getpass("  Password         : ").strip()

    if not username or not password:
        print("  [!] Credentials cannot be empty.")
        return None, None

    os.environ["LEETCODE_USER"] = username
    os.environ["LEETCODE_PASS"] = password

    print(f"  [✓] Credentials set for '{username}'")
    return username, password


def show_menu():
    """
    Display the full interactive menu.

    Returns:
        dict with keys: model, difficulty, start_from, force_download
        or None if user aborts.
    """
    print()
    print("=" * 60)
    print("  ⚡  LeetCode Auto-Solver  ⚡")
    print("=" * 60)

    # ── Ollama Check ──────────────────────────────────────────
    model = _check_ollama_ready()
    if model is None:
        return None

    # ── Login ─────────────────────────────────────────────────
    username, password = ask_credentials()
    if not username:
        return None

    # ── Difficulty ────────────────────────────────────────────
    print("\n  Select difficulty:")
    print("    [1] Easy")
    print("    [2] Medium")
    print("    [3] Hard")

    diff_map = {"1": "EASY", "2": "MEDIUM", "3": "HARD"}
    while True:
        choice = input("\n  Your choice (1/2/3): ").strip()
        if choice in diff_map:
            difficulty = diff_map[choice]
            break
        print("  ✗ Invalid. Enter 1, 2, or 3.")

    # ── Force Download ────────────────────────────────────────
    force_download = False
    force = input("  Force re-download questions? (y/n, default n): ").strip().lower()
    if force == "y":
        force_download = True

    # ── Resume ────────────────────────────────────────────────
    while True:
        raw = input("  Start from question # (default 1): ").strip()
        if not raw:
            start_from = 1
            break
        if raw.isdigit() and int(raw) >= 1:
            start_from = int(raw)
            break
        print("  ✗ Enter a valid question number.")

    # ── Confirm ───────────────────────────────────────────────
    print()
    print("-" * 60)
    print(f"  Model          : {model}")
    print(f"  Username       : {username}")
    print(f"  Difficulty     : {difficulty}")
    print(f"  Force download : {'Yes' if force_download else 'No'}")
    print(f"  Start from     : #{start_from}")
    print("-" * 60)

    confirm = input("  Proceed? (y/n, default y): ").strip().lower()
    if confirm == "n":
        print("  Aborted by user.")
        return None

    return {
        "model": model,
        "difficulty": difficulty,
        "start_from": start_from,
        "force_download": force_download,
    }
