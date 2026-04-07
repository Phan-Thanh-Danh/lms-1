from __future__ import annotations

import time
import uuid

import pytest
from selenium.webdriver.common.by import By

from tests.automation.helpers import backend_exec, lms_url, login, wait_for_text


@pytest.mark.quick
@pytest.mark.smoke
def test_tc26_admin_can_create_user_and_queue_welcome_email(root_dir) -> None:
    email = f"automation.created.{uuid.uuid4().hex[:8]}@example.com"

    backend_exec(
        root_dir,
        f"""
if frappe.db.exists("User", "{email}"):
    frappe.delete_doc("User", "{email}", force=True, ignore_permissions=True)
queue_names = {{
    row.parent
    for row in frappe.get_all(
        "Email Queue Recipient",
        filters={{"recipient": "{email}"}},
        fields=["parent"],
    )
}}
for name in queue_names:
    frappe.delete_doc("Email Queue", name, force=True, ignore_permissions=True)

frappe.conf.max_queued_jobs = 100000
frappe.local.bundled_assets = {{}}
frappe.utils.get_assets_json = lambda: {{}}
frappe.flags.in_import = True
doc = frappe.new_doc("User")
doc.email = "{email}"
doc.first_name = "Created"
doc.last_name = "Student"
doc.user_type = "Website User"
doc.enabled = 1
doc.send_welcome_email = 1
doc.insert(ignore_permissions=True)
result = frappe.db.count("Email Queue Recipient", {{"recipient": "{email}"}})
frappe.db.after_commit.reset()
frappe.flags.in_import = False
        """,
    )

    queue_count = 0
    for _ in range(10):
        queue_count = backend_exec(
            root_dir,
            f"""
result = frappe.db.count("Email Queue Recipient", {{"recipient": "{email}"}})
            """,
        )
        if queue_count:
            break
        time.sleep(1)

    assert queue_count >= 1


@pytest.mark.smoke
def test_tc28_statistics_page_reports_at_least_100_users(driver, base_url: str, seed_data, root_dir) -> None:
    moderator = seed_data["users"]["instructor"]

    login(
        driver,
        base_url,
        moderator["email"],
        moderator["password"],
        redirect_to="/lms/statistics",
    )
    driver.get(lms_url(base_url, "statistics"))

    wait_for_text(driver, "Signups")
    details = backend_exec(
        root_dir,
        """
from lms.lms.api import get_chart_details

result = dict(get_chart_details())
        """,
    )
    assert details["users"] >= 100
