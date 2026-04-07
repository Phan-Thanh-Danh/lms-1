from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.automation.helpers import (
    api_get,
    click_button,
    lms_url,
    login,
    wait_for_text,
)


@pytest.mark.smoke
def test_tc21_enrolled_student_can_access_live_class_join_link(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["batch_user"]
    batch = seed_data["batch"]
    live_class_title = seed_data["live_classes"]["today"]["title"]

    login(
        driver,
        base_url,
        user["email"],
        user["password"],
        redirect_to=f"/lms/batches/{batch['name']}#classes",
    )
    driver.get(lms_url(base_url, f"batches/{batch['name']}#classes"))

    wait_for_text(driver, live_class_title)
    join_link = driver.find_element(
        By.XPATH,
        f"//*[normalize-space()='{live_class_title}']/following::a[normalize-space()='Join'][1]",
    )
    assert "automation-live-class" in join_link.get_attribute("href")


@pytest.mark.smoke
def test_tc24_fast_learner_badge_is_assigned_on_course_completion(
    base_url: str,
    api_session_factory,
    seed_data,
) -> None:
    user = seed_data["users"]["completed_user"]

    session = api_session_factory(user["email"], user["password"])
    badges = api_get(session, base_url, "lms.lms.api.get_badges", params={"member": user["email"]})
    badge_names = {badge["badge"] for badge in badges}

    assert seed_data["badges"]["fast_learner"] in badge_names


@pytest.mark.smoke
def test_tc34_student_can_post_a_comment_in_batch_discussions(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["batch_user"]
    batch = seed_data["batch"]
    comment = f"Automation discussion reply {uuid.uuid4().hex[:8]}"

    login(
        driver,
        base_url,
        user["email"],
        user["password"],
        redirect_to=f"/lms/batches/{batch['name']}#discussions",
    )
    driver.get(lms_url(base_url, f"batches/{batch['name']}#discussions"))

    editor = WebDriverWait(driver, 25).until(
        lambda current_driver: next(
            (
                element
                for element in current_driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
                if element.is_displayed()
            ),
            None,
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", editor)
    editor.click()
    editor.send_keys(comment)
    click_button(driver, "Post")

    wait_for_text(driver, comment)
