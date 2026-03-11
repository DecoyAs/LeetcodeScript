# ⚡ LeetCode Auto-Solver

An automated LeetCode problem solver that uses AI (via [Ollama](https://ollama.com)) to generate solutions, tests them locally, and submits them to LeetCode via Selenium.

> **Disclaimer:** This is a fun curiosity project — not meant to replace actual problem-solving practice!

## Features

- **Interactive CLI** — Guided setup: model selection, login, difficulty, resume
- **Any Ollama Model** — Works with any model you have (DeepSeek, CodeLlama, Qwen, etc.)
- **Auto-Download** — Fetches all questions for a difficulty and caches them locally
- **Resume Support** — Restart from any question number
- **AI Retry Loop** — Re-prompts the AI up to 5 times on failure, feeding errors back
- **Auto-Submit** — Submits passing solutions directly to LeetCode
- **Cross-Platform** — Windows, macOS, Linux

## Prerequisites

| Requirement | Link |
|---|---|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| Google Chrome (latest) | [google.com/chrome](https://www.google.com/chrome/) |
| Ollama | [ollama.com](https://ollama.com/download) |

### Install an Ollama Model

After installing Ollama, pull at least one coding model:

```bash
# Pick one (or more):
ollama pull deepseek-coder:6.7b      # Best quality (~4GB RAM)
ollama pull deepseek-coder:1.3b      # Lighter (~1GB RAM)
ollama pull codellama:7b              # Alternative
ollama pull qwen2.5-coder:7b          # Alternative
```

The script auto-detects your installed models and lets you pick.

## Setup

```bash
# Clone
git clone https://github.com/DecoyAs/LeetcodeScript.git
cd LeetcodeScript

# Virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

The interactive menu guides you through:

1. 🤖 **Ollama check** — verifies installation, lists available models
2. 🔐 **Login** — enter LeetCode username & password
3. 📋 **Difficulty** — Easy / Medium / Hard
4. 📥 **Download** — fetches all questions (cached for future runs)
5. ▶️ **Resume** — pick which question # to start from
6. 🚀 **Auto-solve** — AI generates, judge tests, Selenium submits!

## CAPTCHA / "Not a Human" Troubleshooting

When logging in, LeetCode may show a **"Verify you are human"** check.

If it **fails or gets stuck**:

1. Click **"Troubleshoot"** on the CAPTCHA widget
2. Click **"Submit Response"**
3. If it fails again, repeat — click **"Troubleshoot"** → **"Submit Response"** a second time
4. The page should reload and let you through
5. Once you're logged in, press **ENTER** in the terminal to continue

> This is a known quirk with automated browsers. It usually passes after 1-2 troubleshoot cycles.

## Project Structure

```
LeetcodeScript/
├── main.py              # Entry point
├── cli.py               # Ollama check + model picker + login + menu
├── leetcode_client.py   # LeetCode GraphQL API client
├── question_store.py    # Question caching & resume
├── solver.py            # AI solver with retry loop
├── judge.py             # Local test runner
├── submitter.py         # Selenium-based submission
├── requirements.txt     # Dependencies
├── .gitignore
├── data/                # Cached questions (auto-created)
├── submitted/           # ✓ Passing solutions (auto-created)
└── failed/              # ✗ Failed solutions (auto-created)
```

## How It Works

```
CLI Menu
  ├─ Check Ollama + select model
  ├─ Enter LeetCode credentials
  ├─ Pick difficulty
  ├─ Download all questions → cache to JSON
  └─ Pick starting question #
       ↓
For each problem:
  AI generates solution (Ollama)
       ↓
  Local judge tests against examples
       ↓ FAIL? → Feed error back to AI (up to 5x)
       ↓ PASS? → Submit to LeetCode via Selenium
       ↓
  Next problem
       ↓
Session Summary
```

## Built With

- **Python** — Core language
- **Ollama** — Local AI model inference
- **Selenium** — Browser automation
- **LeetCode GraphQL API** — Problem fetching

## License

MIT
