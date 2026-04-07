from __future__ import annotations

import base64
import json
import os
import shutil
import sys
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from tests.automation.helpers import api_login, lms_url, run_seed

try:
    from pytest_html import extras as html_extras
except Exception:  # pragma: no cover - optional at runtime
    html_extras = None

try:
    from pytest_metadata.plugin import metadata_key
except Exception:  # pragma: no cover - optional at runtime
    metadata_key = None


_CHROMEDRIVER_PATH: str | None = None

ROOT_DIR = Path(__file__).resolve().parents[2]
AUTOMATION_DIR = ROOT_DIR / "tests" / "automation"
REPORTS_DIR = AUTOMATION_DIR / "reports"
ARTIFACTS_DIR = AUTOMATION_DIR / "artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
GENERATED_DIR = ARTIFACTS_DIR / "generated"
SEED_CACHE_PATH = ARTIFACTS_DIR / "seed_data.json"
SEED_LOCK_PATH = ARTIFACTS_DIR / "seed_data.lock"
SEED_WAIT_TIMEOUT = 600
DEFAULT_BASE_URL = "http://lms.localhost:8000"
WINDOWS_CHROME_PATHS = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)
LINUX_CHROME_BINARIES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)
FAKE_PDF = (
    b"%PDF-1.4\n"
    b"%\xe2\xe3\xcf\xd3\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R >>\nendobj\n"
    b"4 0 obj\n<< /Length 45 >>\nstream\nBT /F1 12 Tf 72 120 Td (Automation PDF) Tj ET\nendstream\nendobj\n"
    b"xref\n0 5\n"
    b"0000000000 65535 f \n"
    b"0000000015 00000 n \n"
    b"0000000064 00000 n \n"
    b"0000000121 00000 n \n"
    b"0000000208 00000 n \n"
    b"trailer\n<< /Root 1 0 R /Size 5 >>\nstartxref\n303\n%%EOF\n"
)
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn6N7QAAAAASUVORK5CYII="
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("lms-automation")
    group.addoption(
        "--base-url",
        action="store",
        default=os.getenv("LMS_BASE_URL", DEFAULT_BASE_URL),
        help="Base URL for the LMS instance under test.",
    )
    group.addoption(
        "--headed",
        action="store_true",
        help="Run Chrome in visible mode for debugging.",
    )
    group.addoption(
        "--browser-binary",
        action="store",
        default=os.getenv("LMS_CHROME_BINARY"),
        help="Explicit path to the Chrome/Chromium executable.",
    )


def pytest_configure(config: pytest.Config) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    config.addinivalue_line("markers", "quick: very fast regression checks that avoid heavy seeded data")
    config.addinivalue_line("markers", "smoke: representative LMS coverage with a small, stable subset")
    config.addinivalue_line("markers", "ui_phase2: stateful LMS UI phase-2 E2E flows backed by deterministic seed data")

    if metadata_key is not None:
        metadata = config.stash[metadata_key]
        metadata["Project"] = "Frappe LMS Automation"
        metadata["Base URL"] = config.getoption("--base-url")
        metadata["LMS URL"] = lms_url(config.getoption("--base-url"))
        metadata["Python"] = sys.version.split()[0]
        metadata["Headless"] = str(not config.getoption("--headed"))


def pytest_html_report_title(report) -> None:
    report.title = "Frappe LMS Automation Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or not report.failed:
        return

    driver = item.funcargs.get("driver")
    if driver is None:
        return

    screenshot_path = SCREENSHOTS_DIR / f"{_safe_name(item.nodeid)}.png"
    driver.save_screenshot(str(screenshot_path))

    if html_extras is not None:
        extra = getattr(report, "extras", [])
        extra.append(html_extras.image(str(screenshot_path)))
        report.extras = extra


def _safe_name(nodeid: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in nodeid)


def _detect_chrome_binary(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value

    for binary_name in LINUX_CHROME_BINARIES:
        found = shutil.which(binary_name)
        if found:
            return found

    for path in WINDOWS_CHROME_PATHS:
        if path.exists():
            return str(path)

    return None


def _build_chrome_service() -> Service:
    global _CHROMEDRIVER_PATH

    if _CHROMEDRIVER_PATH is None:
        try:
            _CHROMEDRIVER_PATH = ChromeDriverManager().install()
        except Exception:
            _CHROMEDRIVER_PATH = ""

    if _CHROMEDRIVER_PATH:
        return Service(_CHROMEDRIVER_PATH)

    return Service()


@pytest.fixture(scope="session")
def root_dir() -> Path:
    return ROOT_DIR


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    return pytestconfig.getoption("--base-url").rstrip("/")


@pytest.fixture(scope="session")
def lms_base_url(base_url: str) -> str:
    return lms_url(base_url)


@pytest.fixture(scope="session")
def seed_data() -> dict:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + SEED_WAIT_TIMEOUT

    while time.time() < deadline:
        if SEED_CACHE_PATH.exists():
            return json.loads(SEED_CACHE_PATH.read_text(encoding="utf-8"))

        try:
            with SEED_LOCK_PATH.open("x", encoding="utf-8") as handle:
                handle.write("seed in progress")
        except FileExistsError:
            time.sleep(2)
            continue

        try:
            data = run_seed(ROOT_DIR)
            SEED_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return data
        finally:
            if SEED_LOCK_PATH.exists():
                SEED_LOCK_PATH.unlink()

    raise RuntimeError("Timed out waiting for the shared LMS seed cache.")


@pytest.fixture(scope="session")
def test_files() -> dict[str, Path]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    pdf_path = GENERATED_DIR / "automation-upload.pdf"
    pdf_path.write_bytes(FAKE_PDF)

    exe_path = GENERATED_DIR / "automation-upload.exe"
    exe_path.write_bytes(b"MZ\x90\x00Automation EXE placeholder")

    png_path = GENERATED_DIR / "automation-avatar.png"
    png_path.write_bytes(TINY_PNG)

    return {
        "pdf": pdf_path,
        "exe": exe_path,
        "png": png_path,
    }


@pytest.fixture(scope="session")
def api_session_factory(base_url: str):
    def factory(username: str, password: str):
        return api_login(base_url, username, password)

    return factory


@pytest.fixture()
def download_dir(tmp_path: Path) -> Path:
    download_path = tmp_path / "downloads"
    download_path.mkdir(parents=True, exist_ok=True)
    return download_path


@pytest.fixture()
def driver(pytestconfig: pytest.Config, download_dir: Path):
    chrome_options = Options()
    if not pytestconfig.getoption("--headed"):
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--host-resolver-rules=MAP lms.localhost 127.0.0.1")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        },
    )

    chrome_binary = _detect_chrome_binary(pytestconfig.getoption("--browser-binary"))
    if chrome_binary:
        chrome_options.binary_location = chrome_binary

    service = _build_chrome_service()
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.set_page_load_timeout(30)
    browser.implicitly_wait(2)
    browser.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": str(download_dir)},
    )

    yield browser

    browser.quit()
