from __future__ import annotations

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from tests.automation.helpers import (
    backend_exec,
    click_button,
    find_label_by_text,
    lms_url,
    login,
    wait_for_text,
    wait_for_visible,
)

pytestmark = pytest.mark.ui_phase2


def open_quiz(driver, base_url: str, user: dict[str, str], quiz_name: str) -> None:
    login(driver, base_url, user["email"], user["password"], redirect_to=f"/lms/quiz/{quiz_name}")
    driver.get(lms_url(base_url, f"quiz/{quiz_name}"))


def start_quiz(driver) -> None:
    click_button(driver, "Start")
    wait_for_text(driver, "Question 1")


def reset_quiz_submissions(root_dir, user_email: str, quiz_name: str) -> None:
    backend_exec(
        root_dir,
        f"""
for name in frappe.get_all(
    "LMS Quiz Submission",
    filters={{"member": "{user_email}", "quiz": "{quiz_name}"}},
    pluck="name",
):
    frappe.delete_doc("LMS Quiz Submission", name, force=True, ignore_permissions=True)
result = True
        """,
    )


def answer_review_quiz(driver, answers: list[str]) -> None:
    start_quiz(driver)
    for index, answer in enumerate(answers):
        find_label_by_text(driver, answer).click()
        click_button(driver, "Check")
        if index < len(answers) - 1:
            click_button(driver, "Next")

    click_button(driver, "Submit")
    wait_for_text(driver, "Are you sure you want to submit the quiz?")
    dialog_submit = wait_for_visible(
        driver,
        (
            By.XPATH,
            "(//button[normalize-space()='Submit'])[last()]",
        ),
    )
    dialog_submit.click()
    wait_for_text(driver, "Quiz Summary")


def reset_assignment_submission(root_dir, user_email: str, assignment_name: str) -> None:
    backend_exec(
        root_dir,
        f"""
for name in frappe.get_all(
    "LMS Assignment Submission",
    filters={{"member": "{user_email}", "assignment": "{assignment_name}"}},
    pluck="name",
):
    frappe.delete_doc("LMS Assignment Submission", name, force=True, ignore_permissions=True)
result = True
        """,
    )


def get_assignment_file_input(driver):
    return WebDriverWait(driver, 20).until(
        lambda current_driver: next(
            iter(current_driver.find_elements(By.CSS_SELECTOR, "input[type='file']")),
            None,
        )
    )


def test_ui26_quiz_first_attempt_is_recorded(driver, base_url: str, seed_data, root_dir) -> None:
    user = seed_data["users"]["quiz_attempt_user"]
    quiz = seed_data["quizzes"]["core"]
    answers = [item["correct"] for item in quiz["questions"][:4]] + [quiz["questions"][4]["wrong"]]

    reset_quiz_submissions(root_dir, user["email"], quiz["name"])

    open_quiz(driver, base_url, user, quiz["name"])
    answer_review_quiz(driver, answers)

    submission_count = backend_exec(
        root_dir,
        f"""
result = frappe.db.count("LMS Quiz Submission", {{"quiz": "{quiz["name"]}", "member": "{user["email"]}"}})
        """,
    )
    assert submission_count == 1
    wait_for_text(driver, "Try Again")


def test_ui27_quiz_blocks_after_maximum_attempts(driver, base_url: str, seed_data) -> None:
    user = seed_data["users"]["quiz_max_user"]
    quiz = seed_data["quizzes"]["core"]

    open_quiz(driver, base_url, user, quiz["name"])
    wait_for_text(driver, "maximum number of attempts")


def test_ui28_quiz_score_summary_shows_eighty_percent(driver, base_url: str, seed_data, root_dir) -> None:
    user = seed_data["users"]["quiz_score_user"]
    quiz = seed_data["quizzes"]["core"]
    answers = [item["correct"] for item in quiz["questions"][:4]] + [quiz["questions"][4]["wrong"]]

    reset_quiz_submissions(root_dir, user["email"], quiz["name"])

    open_quiz(driver, base_url, user, quiz["name"])
    answer_review_quiz(driver, answers)

    wait_for_text(driver, "You got 80% correct answers")


def test_ui29_assignment_accepts_pdf_upload(driver, base_url: str, seed_data, test_files, root_dir) -> None:
    user = seed_data["users"]["course_user"]
    assignment = seed_data["assignment"]
    reset_assignment_submission(root_dir, user["email"], assignment["name"])

    login(
        driver,
        base_url,
        user["email"],
        user["password"],
        redirect_to=f"/lms/assignment-submission/{assignment['name']}/new",
    )
    driver.get(lms_url(base_url, f"assignment-submission/{assignment['name']}/new"))

    file_input = get_assignment_file_input(driver)
    file_input.send_keys(str(test_files["pdf"]))
    click_button(driver, "Save")

    WebDriverWait(driver, 20).until(lambda current_driver: "/new" not in current_driver.current_url)

    submission_exists = backend_exec(
        root_dir,
        f"""
result = frappe.db.exists(
    "LMS Assignment Submission",
    {{"member": "{user["email"]}", "assignment": "{assignment["name"]}"}},
)
        """,
    )
    assert submission_exists


def test_ui30_assignment_rejects_exe_upload(driver, base_url: str, seed_data, test_files, root_dir) -> None:
    user = seed_data["users"]["course_user"]
    assignment = seed_data["assignment"]
    reset_assignment_submission(root_dir, user["email"], assignment["name"])

    login(
        driver,
        base_url,
        user["email"],
        user["password"],
        redirect_to=f"/lms/assignment-submission/{assignment['name']}/new",
    )
    driver.get(lms_url(base_url, f"assignment-submission/{assignment['name']}/new"))

    file_input = get_assignment_file_input(driver)
    file_input.send_keys(str(test_files["exe"]))

    wait_for_text(driver, "Only PDF files are allowed.")
    assert driver.current_url.endswith("/new")
