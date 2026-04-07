from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.automation.helpers import backend_exec, click_button, lms_url, login, wait_for_text, wait_for_visible

pytestmark = pytest.mark.ui_phase2


def create_comment_notification(root_dir, user_email: str) -> dict[str, str]:
    token = uuid.uuid4().hex[:8]
    subject = f"Automation comment notification {token}"
    detail = f"Automation notification detail {token}"

    return backend_exec(
        root_dir,
        f"""
for name in frappe.get_all(
    "Notification Log",
    filters={{"for_user": "{user_email}", "subject": ["like", "Automation comment notification %"]}},
    pluck="name",
):
    frappe.delete_doc("Notification Log", name, force=True, ignore_permissions=True)

doc = frappe.get_doc(
    {{
        "doctype": "Notification Log",
        "subject": "{subject}",
        "email_content": "<p>{detail}</p>",
        "for_user": "{user_email}",
        "from_user": "Administrator",
        "type": "Alert",
        "read": 0,
    }}
)
doc.insert(ignore_permissions=True)
result = {{"name": doc.name, "subject": doc.subject, "detail": "{detail}"}}
        """,
    )


def get_notification_row(driver, subject: str):
    return wait_for_visible(
        driver,
        (
            By.XPATH,
            f"//*[contains(normalize-space(), '{subject}')]/ancestor::div[contains(@class, 'space-y-1.5')][1]",
        ),
    )


def test_ui24_notification_list_shows_backend_created_unread_item(
    driver,
    base_url: str,
    seed_data,
    root_dir,
) -> None:
    user = seed_data["users"]["batch_user"]
    notification = create_comment_notification(root_dir, user["email"])

    login(driver, base_url, user["email"], user["password"], redirect_to="/lms/notifications")
    driver.get(lms_url(base_url, "notifications"))

    wait_for_text(driver, notification["subject"])
    wait_for_text(driver, notification["detail"])
    get_notification_row(driver, notification["subject"])


def test_ui25_notification_can_move_from_unread_to_read(
    driver,
    base_url: str,
    seed_data,
    root_dir,
) -> None:
    user = seed_data["users"]["course_user"]
    notification = create_comment_notification(root_dir, user["email"])

    login(driver, base_url, user["email"], user["password"], redirect_to="/lms/notifications")
    driver.get(lms_url(base_url, "notifications"))

    row = get_notification_row(driver, notification["subject"])
    wait_for_text(driver, notification["detail"])

    mark_as_read_button = row.find_element(By.XPATH, ".//button")
    driver.execute_script("arguments[0].click();", mark_as_read_button)

    WebDriverWait(driver, 20).until(
        lambda current_driver, subject=notification["subject"]: subject not in current_driver.page_source
    )

    click_button(driver, "Read")
    wait_for_text(driver, notification["subject"])
    wait_for_text(driver, notification["detail"])

    read_value = backend_exec(
        root_dir,
        f"""
result = frappe.db.get_value("Notification Log", "{notification["name"]}", "read")
        """,
    )
    assert int(read_value) == 1
