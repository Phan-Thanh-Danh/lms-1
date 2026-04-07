from __future__ import annotations

import json
import subprocess
import textwrap
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

import requests
from pypdf import PdfReader
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


LMS_BASE_PATH = "/lms"
BACKEND_MARKER = "__LMS_AUTOMATION_JSON__"
SEED_MARKER = "__LMS_AUTOMATION_SEED__"


def lms_url(base_url: str, path: str = "") -> str:
    path = path.strip("/")
    if not path:
        return f"{base_url}{LMS_BASE_PATH}"
    return f"{base_url}{LMS_BASE_PATH}/{path}"


def login(driver: WebDriver, base_url: str, username: str, password: str, redirect_to: str = "/lms") -> None:
    redirect_target = quote(redirect_to, safe="/:?=&")
    driver.get(f"{base_url}/login?redirect-to={redirect_target}")

    wait = WebDriverWait(driver, 20)
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "login_email")))
    password_input = wait.until(EC.visibility_of_element_located((By.ID, "login_password")))
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login")))

    clear_and_type(email_input, username)
    clear_and_type(password_input, password)
    login_button.click()

    wait.until(lambda current_driver: "/login" not in current_driver.current_url.rstrip("/"))


def clear_and_type(element, value: str) -> None:
    element.clear()
    element.send_keys(value)


def wait_for_visible(driver: WebDriver, locator: tuple[str, str], timeout: int = 20):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


def wait_for_clickable(driver: WebDriver, locator: tuple[str, str], timeout: int = 20):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))


def wait_for_text(driver: WebDriver, text: str, timeout: int = 20) -> None:
    WebDriverWait(driver, timeout).until(
        lambda current_driver: text in current_driver.page_source
    )


def click_button(driver: WebDriver, text: str, timeout: int = 20) -> None:
    locator = (
        By.XPATH,
        f"//button[normalize-space()='{text}' or .//*[normalize-space()='{text}']]",
    )
    wait_for_clickable(driver, locator, timeout).click()


def click_sidebar_button(driver: WebDriver, text: str, timeout: int = 20) -> None:
    locator = (
        By.XPATH,
        f"//nav//button[.//span[normalize-space()='{text}']]",
    )
    button = wait_for_clickable(driver, locator, timeout)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    driver.execute_script("arguments[0].click();", button)


def navigate_sidebar_to_path(
    driver: WebDriver,
    text: str,
    expected_path: str,
    timeout: int = 20,
) -> None:
    locator = (
        By.XPATH,
        f"//nav//button[.//span[normalize-space()='{text}']]",
    )
    button = wait_for_clickable(driver, locator, timeout)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)

    attempts = [
        lambda current_button: current_button.click(),
        lambda current_button: ActionChains(driver).move_to_element(current_button).click().perform(),
        lambda current_button: current_button.send_keys(Keys.ENTER),
        lambda current_button: driver.execute_script("arguments[0].click();", current_button),
    ]

    for attempt in attempts:
        attempt(button)
        try:
            WebDriverWait(driver, 5).until(
                lambda current_driver: expected_path in current_driver.current_url
            )
            return
        except TimeoutException:
            button = wait_for_clickable(driver, locator, timeout)

    raise AssertionError(
        f"Sidebar navigation for '{text}' did not reach '{expected_path}'. Final URL: {driver.current_url}"
    )


def click_link(driver: WebDriver, text: str, timeout: int = 20) -> None:
    locator = (By.XPATH, f"//a[normalize-space()='{text}' or .//*[normalize-space()='{text}']]")
    wait_for_clickable(driver, locator, timeout).click()


def find_label_by_text(driver: WebDriver, text: str, timeout: int = 20):
    locator = (By.XPATH, f"//label[.//*[contains(normalize-space(), '{text}')] or contains(normalize-space(), '{text}')]")
    return wait_for_clickable(driver, locator, timeout)


def _api_base_url(base_url: str) -> str:
    parsed = urlsplit(base_url)
    if parsed.hostname != "lms.localhost":
        return base_url

    connect_netloc = parsed.netloc.replace("lms.localhost", "localhost")
    return f"{parsed.scheme}://{connect_netloc}"


def _api_headers(base_url: str) -> dict[str, str]:
    parsed = urlsplit(base_url)
    if parsed.hostname != "lms.localhost":
        return {}

    return {"Host": parsed.netloc}


def api_login(base_url: str, username: str, password: str) -> requests.Session:
    session = requests.Session()
    response = session.post(
        f"{_api_base_url(base_url)}/api/method/login",
        data={"usr": username, "pwd": password},
        headers=_api_headers(base_url),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("message") not in {"Logged In", "No App"} and "home_page" not in payload:
        raise RuntimeError(f"Unexpected login response: {payload}")
    return session


def api_post(session: requests.Session, base_url: str, method: str, data: dict[str, Any] | None = None) -> Any:
    response = session.post(
        f"{_api_base_url(base_url)}/api/method/{method}",
        data=data or {},
        headers=_api_headers(base_url),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("message", payload)


def api_get(session: requests.Session, base_url: str, method: str, params: dict[str, Any] | None = None) -> Any:
    response = session.get(
        f"{_api_base_url(base_url)}/api/method/{method}",
        params=params or {},
        headers=_api_headers(base_url),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("message", payload)


def run_seed(root_dir: Path) -> dict[str, Any]:
    script_path = root_dir / "tests" / "automation" / "seed_lms_data.py"
    script_text = script_path.read_text(encoding="utf-8")
    command = [
        "docker",
        "exec",
        "lms-frappe-1",
        "bash",
        "-lc",
        (
            "cd /home/frappe/frappe-bench && "
            "source /home/frappe/frappe-bench/env/bin/activate && "
            "python - <<'PY'\n"
            f"{script_text}\n"
            "PY"
        ),
    ]
    completed = subprocess.run(
        command,
        cwd=root_dir,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Failed to seed LMS data.\n"
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        )
    if SEED_MARKER not in completed.stdout:
        raise RuntimeError(
            "Seed helper did not return structured output.\n"
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        )

    raw_payload = completed.stdout.split(SEED_MARKER)[-1].strip().splitlines()[0]
    return json.loads(raw_payload)


def backend_exec(root_dir: Path, code: str, timeout: int = 120) -> Any:
    user_code = textwrap.indent(textwrap.dedent(code).strip(), "    ")
    python_script = "\n".join(
        [
            "import json",
            "import traceback",
            "",
            "import frappe",
            "",
            'frappe.init(site="lms.localhost", sites_path="/home/frappe/frappe-bench/sites")',
            "frappe.connect()",
            "result = None",
            "error = None",
            "try:",
            user_code,
            "    frappe.db.commit()",
            "except Exception as exc:",
            "    frappe.db.rollback()",
            '    error = {"type": exc.__class__.__name__, "message": str(exc)}',
            "    traceback.print_exc()",
            "finally:",
            "    frappe.destroy()",
            "",
            f'print("{BACKEND_MARKER}" + json.dumps({{"result": result, "error": error}}, default=str))',
        ]
    )

    command = [
        "docker",
        "exec",
        "lms-frappe-1",
        "bash",
        "-lc",
        (
            "cd /home/frappe/frappe-bench && "
            "source /home/frappe/frappe-bench/env/bin/activate && "
            "python - <<'PY'\n"
            f"{python_script}\n"
            "PY"
        ),
    ]

    completed = subprocess.run(
        command,
        cwd=root_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if BACKEND_MARKER not in completed.stdout:
        raise RuntimeError(
            "Backend helper did not return structured output.\n"
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        )

    raw_payload = completed.stdout.split(BACKEND_MARKER)[-1].strip().splitlines()[0]
    payload = json.loads(raw_payload)
    if completed.returncode != 0 or payload.get("error"):
        raise RuntimeError(
            "Backend helper failed.\n"
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        )
    return payload.get("result")


def wait_for_download(download_dir: Path, filename_fragment: str, timeout: int = 20) -> Path:
    deadline = time.time() + timeout
    last_seen: Path | None = None
    while time.time() < deadline:
        for candidate in download_dir.glob("*"):
            if filename_fragment in candidate.name and candidate.suffix != ".crdownload":
                if candidate.stat().st_size > 0:
                    return candidate
                last_seen = candidate
        time.sleep(0.5)

    raise TimeoutException(f"Timed out waiting for download containing '{filename_fragment}'. Last seen: {last_seen}")


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
