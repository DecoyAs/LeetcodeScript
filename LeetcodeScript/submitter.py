"""
LeetCode submission module.
Handles Chrome WebDriver setup, LeetCode login, and solution submission.
Cross-platform: works on Windows, macOS, and Linux.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import platform


def _warn_if_chrome_running():
    """Warn the user if Chrome is already running (cross-platform)."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                print("\n" + "=" * 60)
                print("  ⚠  Google Chrome is currently running!")
                print("  If you get a 'SessionNotCreatedException',")
                print("  close Chrome and try again.")
                print("=" * 60 + "\n")
                return
    except ImportError:
        # psutil not installed — try platform-specific fallback
        system = platform.system()
        try:
            if system == "Windows":
                import subprocess
                output = subprocess.check_output(
                    'tasklist /FI "IMAGENAME eq chrome.exe"',
                    shell=True, text=True
                )
                if 'chrome.exe' in output.lower():
                    print("\n  ⚠  Chrome is running. Close it if driver fails.\n")
            elif system in ("Linux", "Darwin"):
                import subprocess
                result = subprocess.run(
                    ["pgrep", "-x", "chrome"], capture_output=True
                )
                if result.returncode == 0:
                    print("\n  ⚠  Chrome is running. Close it if driver fails.\n")
        except Exception:
            pass


def _kill_stale_drivers():
    """Kill any leftover chromedriver processes (cross-platform)."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'chromedriver' in proc.info['name'].lower():
                proc.kill()
        return
    except ImportError:
        pass

    # Fallback without psutil
    system = platform.system()
    try:
        import subprocess
        if system == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/IM", "chromedriver.exe", "/T"],
                capture_output=True,
            )
        else:
            subprocess.run(["pkill", "-f", "chromedriver"], capture_output=True)
    except Exception:
        pass


def get_driver():
    """
    Launch a headless-ready Chrome WebDriver with bot-detection evasion.

    Returns:
        webdriver.Chrome instance, or None on failure.
    """
    _warn_if_chrome_running()
    _kill_stale_drivers()

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Evasion: bypass Cloudflare / bot-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    print("  Launching Chrome driver...")
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception as e:
        print(f"\n  [!] CRITICAL: Failed to launch Chrome!")
        print(f"      {e}")
        print("      Make sure Chrome and chromedriver are installed.")
        return None
    return driver


def login_to_leetcode(driver):
    """
    Log into LeetCode using credentials from environment variables.
    The user must set LEETCODE_USER and LEETCODE_PASS before running.
    Supports manual CAPTCHA solving.

    Returns:
        True if login succeeded, False otherwise.
    """
    username = os.environ.get("LEETCODE_USER")
    password = os.environ.get("LEETCODE_PASS")

    if not username or not password:
        print("\n" + "=" * 60)
        print("  LOGIN CREDENTIALS REQUIRED!")
        print("  Set these environment variables before running:")
        print()
        if platform.system() == "Windows":
            print('    $env:LEETCODE_USER="your_email"')
            print('    $env:LEETCODE_PASS="your_password"')
        else:
            print('    export LEETCODE_USER="your_email"')
            print('    export LEETCODE_PASS="your_password"')
        print("=" * 60 + "\n")
        return False

    print("  Logging into LeetCode...")
    try:
        driver.get("https://leetcode.com/accounts/login/")
        wait = WebDriverWait(driver, 15)

        # Fill credentials
        print("  > Entering credentials...")
        user_field = wait.until(EC.presence_of_element_located((By.ID, "id_login")))
        user_field.send_keys(username)

        pass_field = driver.find_element(By.ID, "id_password")
        pass_field.send_keys(password)
        time.sleep(1)

        # Click sign in
        print("  > Clicking submit...")
        try:
            sign_in_btn = driver.find_element(By.ID, "signin_btn")
            sign_in_btn.click()
        except Exception:
            print("    (Could not auto-click sign in. Please click it manually.)")

        print("  > Waiting for login. IF A CAPTCHA APPEARS, SOLVE IT MANUALLY...")
        input("\n  >>> Press ENTER after you have successfully logged in <<<\n")
        print("  > Login confirmed!\n")

        # Set default language to Python 3
        try:
            driver.get("https://leetcode.com/")
            time.sleep(2)
            driver.execute_script("window.localStorage.setItem('global_lang', 'python3');")
        except Exception:
            pass

        return True
    except Exception as e:
        print(f"  [!] Login failed: {e}")
        return False


def submit_to_leetcode(driver, slug, code):
    """
    Submit a solution to LeetCode for a given problem.

    Args:
        driver: active Selenium WebDriver
        slug: problem slug (e.g. "two-sum")
        code: Python solution code

    Returns:
        True if submission was triggered, False on error.
    """
    if not driver:
        print("  [!] Driver not initialized! Cannot submit.")
        return False

    try:
        _ = driver.window_handles
    except Exception:
        print("  [!] Browser was closed! Aborting.")
        return False

    try:
        driver.get(f"https://leetcode.com/problems/{slug}/")
        wait = WebDriverWait(driver, 30)

        print("    Waiting for editor to load...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "view-lines")))
        time.sleep(2)

        # Inject code via Monaco editor API
        print("    Injecting solution...")
        encoded_code = code.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        js_script = f"""
            try {{
                var models = monaco.editor.getModels();
                if (models.length > 0) {{
                    models[0].setValue(`{encoded_code}`);
                    return true;
                }}
                return false;
            }} catch(e) {{
                return false;
            }}
        """
        success = driver.execute_script(js_script)
        if not success:
            print("    ⚠ Monaco injection may have failed.")
        time.sleep(1)

        # Click Submit button
        print("    Clicking Submit...")
        submit_btn = None
        xpath_selectors = [
            "//button[contains(@data-e2e-locator, 'console-submit-button')]",
            "//button[contains(@data-cy, 'submit-code-btn')]",
            "//button[descendant::text()[contains(., 'Submit')]]",
        ]

        for xpath in xpath_selectors:
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                break
            except Exception:
                continue

        if not submit_btn:
            raise Exception("Submit button not found on page.")

        submit_btn.click()
        print("    ✓ Submitted! Waiting for LeetCode to judge...")
        time.sleep(10)
        return True

    except Exception as e:
        print(f"    [!] Submission error: {e}")
        return False