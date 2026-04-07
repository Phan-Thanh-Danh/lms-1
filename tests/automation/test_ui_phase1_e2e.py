from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tests.automation.helpers import login, navigate_sidebar_to_path, wait_for_visible

pytestmark = pytest.mark.ui_phase1

ADMIN_USER = "Administrator"
ADMIN_PASSWORD = "admin"

def login_admin_to_lms(driver, base_url: str) -> None:
    login(driver, base_url, ADMIN_USER, ADMIN_PASSWORD, redirect_to="/lms")
    WebDriverWait(driver, 20).until(lambda current_driver: "/lms" in current_driver.current_url)
    wait_for_visible(driver, (By.XPATH, "//nav"))

def open_user_menu(driver) -> None:
    locator = (
        By.XPATH,
        "(//button[contains(@class, 'h-12') and (.//*[contains(normalize-space(), 'Administrator')] or .//*[contains(normalize-space(), 'Learning')])])[1]",
    )
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(locator)).click()

def click_menu_item(driver, label: str) -> None:
    locator = (
        By.XPATH,
        f"//button[normalize-space()='{label}' or .//*[normalize-space()='{label}']]",
    )
    button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].click();", button)

def test_ui01_login_page_renders_core_controls(driver, base_url: str) -> None:
    driver.get(f"{base_url}/login")
    wait_for_visible(driver, (By.ID, "login_email"))
    wait_for_visible(driver, (By.ID, "login_password"))
    wait_for_visible(driver, (By.CSS_SELECTOR, "button.btn-login"))

def test_ui02_admin_can_enter_lms_and_see_core_sidebar(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    for label in ("Home", "Search", "Notifications", "Courses", "Programs", "Batches", "Statistics"):
        wait_for_visible(driver, (By.XPATH, f"//nav//span[normalize-space()='{label}']"))

def test_ui03_sidebar_opens_courses_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Courses", "/lms/courses")
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='All Courses']"))

def test_ui04_sidebar_opens_programs_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Programs", "/lms/programs")
    # Verify we are on the correct page by checking the header button
    wait_for_visible(driver, (By.XPATH, "//header//button[normalize-space()='New']"))
    # Acceptance criteria: either see the "No programs" empty state or some program count like "1 Program" or "All Programs"
    wait_for_visible(
        driver,
        (
            By.XPATH,
            "//*[contains(normalize-space(), 'programs') or contains(normalize-space(), 'Program')]",
        ),
    )

def test_ui05_sidebar_opens_batches_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Batches", "/lms/batches")
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='All Batches']"))

def test_ui06_sidebar_opens_search_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Search", "/lms/search")
    search_input = wait_for_visible(driver, (By.CSS_SELECTOR, "input[placeholder='Search for a keyword or phrase and press enter']"))
    query = f"ui-phase1-{uuid.uuid4().hex}"
    search_input.send_keys(query)
    WebDriverWait(driver, 20).until(
        lambda current_driver, query=query: current_driver.find_element(
            By.CSS_SELECTOR,
            "input[placeholder='Search for a keyword or phrase and press enter']",
        ).get_attribute("value")
        == query
    )
    wait_for_visible(driver, (By.XPATH, "//*[contains(normalize-space(), 'Press enter to search')]"))

def test_ui07_sidebar_opens_notifications_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Notifications", "/lms/notifications")
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='Unread']"))
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='Read']"))

def test_ui08_sidebar_opens_statistics_page(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    navigate_sidebar_to_path(driver, "Statistics", "/lms/statistics")
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='Signups']"))
    wait_for_visible(driver, (By.XPATH, "//*[normalize-space()='Enrollments']"))

def test_ui09_user_menu_can_toggle_theme(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    driver.execute_script("document.documentElement.setAttribute('data-theme', 'light'); localStorage.setItem('theme', 'light');")
    open_user_menu(driver)
    click_menu_item(driver, "Toggle Theme")
    WebDriverWait(driver, 20).until(
        lambda current_driver: current_driver.execute_script(
            "return document.documentElement.getAttribute('data-theme')"
        ) == "dark"
    )

def test_ui10_user_can_log_out_from_user_menu(driver, base_url: str) -> None:
    login_admin_to_lms(driver, base_url)
    open_user_menu(driver)
    click_menu_item(driver, "Log out")
    WebDriverWait(driver, 20).until(
        lambda current_driver: (current_driver.get_cookie("user_id") or {}).get("value") == "Guest"
    )
    WebDriverWait(driver, 20).until(
        lambda current_driver: not current_driver.find_elements(
            By.XPATH,
            "//nav//span[normalize-space()='Notifications']",
        )
    )
