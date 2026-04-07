from __future__ import annotations

import re

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.automation.helpers import api_login, api_post, backend_exec, lms_url, login, wait_for_text, wait_for_visible

pytestmark = pytest.mark.ui_phase2


def reset_course_progress(root_dir, user_email: str, course_name: str) -> None:
    backend_exec(
        root_dir,
        f"""
for name in frappe.get_all(
    "LMS Course Progress",
    filters={{"member": "{user_email}", "course": "{course_name}"}},
    pluck="name",
):
    frappe.delete_doc("LMS Course Progress", name, force=True, ignore_permissions=True)

enrollment = frappe.get_doc("LMS Enrollment", {{"member": "{user_email}", "course": "{course_name}"}})
enrollment.progress = 0
enrollment.current_lesson = None
enrollment.save(ignore_permissions=True)
result = enrollment.name
        """,
    )


def reset_course_enrollment(root_dir, user_email: str, course_name: str) -> None:
    backend_exec(
        root_dir,
        f"""
for name in frappe.get_all(
    "LMS Course Progress",
    filters={{"member": "{user_email}", "course": "{course_name}"}},
    pluck="name",
):
    frappe.delete_doc("LMS Course Progress", name, force=True, ignore_permissions=True)

for name in frappe.get_all(
    "LMS Enrollment",
    filters={{"member": "{user_email}", "course": "{course_name}"}},
    pluck="name",
):
    frappe.delete_doc("LMS Enrollment", name, force=True, ignore_permissions=True)

result = True
        """,
    )


def get_completion_percentage(driver) -> int:
    elements = driver.find_elements(
        By.XPATH,
        "//*[contains(normalize-space(), '%') and contains(normalize-space(), 'completed')]",
    )
    for element in elements:
        if not element.is_displayed():
            continue
        match = re.search(r"(\d+)\s*%\s*completed", element.text.lower())
        if match:
            return int(match.group(1))
    return 0


def click_start_learning(driver) -> None:
    locator = (
        By.XPATH,
        "//button[normalize-space()='Start Learning' or .//*[normalize-space()='Start Learning']]",
    )
    WebDriverWait(driver, 20).until(lambda current_driver: current_driver.find_elements(*locator))
    buttons = driver.find_elements(*locator)

    for button in buttons:
        if not button.is_displayed():
            continue
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        driver.execute_script("arguments[0].click();", button)
        return

    driver.execute_script("arguments[0].click();", buttons[-1])


def test_ui21_student_can_enroll_in_free_course(driver, base_url: str, seed_data, root_dir) -> None:
    user = seed_data["users"]["free_enroll_user"]
    course = seed_data["courses"]["free"]

    reset_course_enrollment(root_dir, user["email"], course["name"])

    login(driver, base_url, user["email"], user["password"], redirect_to=f"/lms/courses/{course['name']}")
    driver.get(lms_url(base_url, f"courses/{course['name']}"))
    click_start_learning(driver)

    WebDriverWait(driver, 20).until(
        lambda current_driver: f"/courses/{course['name']}/learn/{course['video_route']}" in current_driver.current_url
    )

    enrollment_exists = backend_exec(
        root_dir,
        f"""
result = frappe.db.exists(
    "LMS Enrollment",
    {{"member": "{user["email"]}", "course": "{course["name"]}"}},
)
        """,
    )
    assert enrollment_exists


def test_ui22_lesson_page_auto_updates_progress_for_enrolled_student(
    driver,
    base_url: str,
    seed_data,
    root_dir,
) -> None:
    user = seed_data["users"]["course_user"]
    course = seed_data["courses"]["free"]

    reset_course_progress(root_dir, user["email"], course["name"])

    session = api_login(base_url, user["email"], user["password"])
    api_post(
        session,
        base_url,
        "lms.lms.doctype.course_lesson.course_lesson.save_progress",
        data={
            "lesson": course["formatted_lesson"],
            "course": course["name"],
        },
    )

    login(
        driver,
        base_url,
        user["email"],
        user["password"],
        redirect_to=f"/lms/courses/{course['name']}/learn/{course['formatted_route']}",
    )
    driver.get(lms_url(base_url, f"courses/{course['name']}/learn/{course['formatted_route']}"))

    WebDriverWait(driver, 20).until(lambda current_driver: get_completion_percentage(current_driver) > 0)

    progress_value = backend_exec(
        root_dir,
        f"""
result = frappe.db.get_value(
    "LMS Enrollment",
    {{"member": "{user["email"]}", "course": "{course["name"]}"}},
    "progress",
)
        """,
    )

    assert float(progress_value) > 0
    assert get_completion_percentage(driver) > 0


def test_ui23_completed_student_sees_certificate_button(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["completed_user"]
    course = seed_data["courses"]["free"]

    login(driver, base_url, user["email"], user["password"], redirect_to=f"/lms/courses/{course['name']}")
    driver.get(lms_url(base_url, f"courses/{course['name']}"))

    wait_for_text(driver, "Get Certificate")
