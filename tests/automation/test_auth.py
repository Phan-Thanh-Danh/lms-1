from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.quick
@pytest.mark.smoke
def test_tc01_login_redirects_to_dashboard(driver, base_url: str) -> None:
    driver.get(f"{base_url}/login")

    wait = WebDriverWait(driver, 20)
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "login_email")))
    password_input = wait.until(EC.visibility_of_element_located((By.ID, "login_password")))
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-login")))

    email_input.clear()
    email_input.send_keys("Administrator")
    password_input.clear()
    password_input.send_keys("admin")
    login_button.click()

    wait.until(lambda current_driver: "/login" not in current_driver.current_url.rstrip("/"))

    final_url = driver.current_url.lower()
    assert any(token in final_url for token in ("/app", "/desk", "desk")), (
        f"Expected redirect to dashboard, but got: {driver.current_url}"
    )
