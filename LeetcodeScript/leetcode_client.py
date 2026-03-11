"""
LeetCode API client.
Fetches problem lists and problem details via the LeetCode GraphQL API.
"""

import requests

LEETCODE_API = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}


def _get_total_count(difficulty):
    """Get the total number of problems available for a difficulty."""
    query = """
    query problemsetQuestionList($filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(categorySlug: "", limit: 1, filters: $filters) {
        totalNum
      }
    }
    """
    variables = {"filters": {"difficulty": difficulty}}
    try:
        r = requests.post(
            LEETCODE_API,
            json={"query": query, "variables": variables},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["data"]["problemsetQuestionList"]["totalNum"]
    except Exception:
        return 500  # Safe fallback


def get_problems(difficulty="EASY", limit=None):
    """
    Fetch ALL problems of a given difficulty from LeetCode.

    Args:
        difficulty: "EASY", "MEDIUM", or "HARD"
        limit: max number (None = fetch ALL available)

    Returns:
        list of dicts with keys: title, titleSlug, difficulty
    """
    if limit is None:
        limit = _get_total_count(difficulty)
        print(f"  Found {limit} total {difficulty.lower()} problems on LeetCode.")

    query = """
    query problemsetQuestionList($limit: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(categorySlug: "", limit: $limit, filters: $filters) {
        questions: data { title titleSlug difficulty }
      }
    }
    """
    variables = {"limit": limit, "filters": {"difficulty": difficulty}}
    try:
        r = requests.post(
            LEETCODE_API,
            json={"query": query, "variables": variables},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"]["problemsetQuestionList"]["questions"]
    except requests.exceptions.Timeout:
        print("  [!] LeetCode API timed out. Try again later.")
        raise
    except requests.exceptions.RequestException as e:
        print(f"  [!] API request failed: {e}")
        raise


def get_problem_details(slug):
    """
    Fetch full details for a single problem by its slug.

    Returns:
        dict with keys: title, content, exampleTestcases, codeSnippets
    """
    query = """
    query getQuestion($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        title content exampleTestcases
        codeSnippets { lang langSlug code }
      }
    }
    """
    try:
        r = requests.post(
            LEETCODE_API,
            json={"query": query, "variables": {"titleSlug": slug}},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["data"]["question"]
    except requests.exceptions.Timeout:
        print("  [!] LeetCode API timed out!")
        raise
    except requests.exceptions.RequestException as e:
        print(f"  [!] API request failed: {e}")
        raise