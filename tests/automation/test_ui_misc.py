from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By

from tests.automation.helpers import lms_url, login, navigate_sidebar_to_path, wait_for_text


@pytest.mark.smoke
def test_tc29_homepage_renders_cleanly_on_iphone_13_viewport(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["course_user"]

    driver.set_window_size(390, 844)
    login(driver, base_url, user["email"], user["password"], redirect_to="/lms")
    driver.get(lms_url(base_url))

    wait_for_text(driver, "Resume where you left off")
    mobile_nav = driver.find_element(By.CSS_SELECTOR, "div.fixed.bottom-0.left-0.w-full")
    assert mobile_nav.is_displayed()

    scroll_width = driver.execute_script("return document.documentElement.scrollWidth")
    inner_width = driver.execute_script("return window.innerWidth")
    assert scroll_width <= inner_width + 5


@pytest.mark.smoke
def test_tc53_sidebar_navigation_opens_core_lms_sections(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["course_user"]

    login(driver, base_url, user["email"], user["password"], redirect_to="/lms")
    driver.get(lms_url(base_url))

    for label, expected_path in (
        ("Courses", "/lms/courses"),
        ("Batches", "/lms/batches"),
        ("Statistics", "/lms/statistics"),
    ):
        navigate_sidebar_to_path(driver, label, expected_path)
