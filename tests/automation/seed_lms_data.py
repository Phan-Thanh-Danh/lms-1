from __future__ import annotations

import base64
import json
from pathlib import Path

import frappe
from frappe.utils import add_days, now, nowdate
from frappe.utils.password import update_password

from lms.lms.api import delete_batch, delete_course
from lms.lms.doctype.course_lesson.course_lesson import save_progress
from lms.lms.doctype.lms_certificate.lms_certificate import get_default_certificate_template
from lms.lms.doctype.lms_quiz.lms_quiz import submit_quiz
from lms.sqlite import build_index


OUTPUT_PATH = Path("/workspace/tests/automation/artifacts/seed_data.json")
AUTOMATION_PREFIX = "Automation "
AUTOMATION_EMAIL_PREFIX = "automation."
USER_PASSWORD = "Automation@123"
OUTGOING_ACCOUNT_NAME = "Automation Outgoing Email"
SEED_MARKER = "__LMS_AUTOMATION_SEED__"

TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn6N7QAAAAASUVORK5CYII="
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


def main() -> None:
    frappe.init(site="lms.localhost", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.conf.max_queued_jobs = 100000

    frappe.flags.in_import = True
    cleanup_automation_records()
    frappe.flags.in_import = False
    ensure_outgoing_email_account()
    configure_lms_settings()

    files = {
        "guide_pdf_url": create_public_file("automation-guide.pdf", FAKE_PDF),
        "avatar_png_url": create_public_file("automation-avatar.png", TINY_PNG),
        "badge_png_url": create_public_file("automation-badge.png", TINY_PNG),
    }

    frappe.flags.in_import = True
    users = create_users(files["avatar_png_url"])
    frappe.flags.in_import = False
    courses = create_courses(users["instructor"], files)
    quizzes = create_quizzes()
    assignment = create_assignment()
    badges = create_badges(files["badge_png_url"])
    program = create_program(courses)
    batch, live_classes = create_batch_and_live_classes(courses, users["instructor"])

    create_course_enrollment(users["course_user"], courses["free"])
    create_course_enrollment(users["completed_user"], courses["free"])
    create_batch_enrollment(users["batch_user"], batch)

    complete_course_for_user(users["completed_user"]["email"], courses["free"])
    create_quiz_attempts(quizzes, users, badges)
    create_search_index()

    payload = {
        "users": users,
        "files": files,
        "courses": courses,
        "quizzes": quizzes,
        "assignment": assignment,
        "program": program,
        "batch": batch,
        "live_classes": live_classes,
        "badges": badges,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(SEED_MARKER + json.dumps(payload))
    frappe.db.commit()
    frappe.destroy()


def cleanup_automation_records() -> None:
    queue_names = {
        row.parent
        for row in frappe.get_all(
            "Email Queue Recipient",
            filters={"recipient": ["like", f"%{AUTOMATION_EMAIL_PREFIX}%"]},
            fields=["parent"],
        )
    }
    for name in queue_names:
        frappe.delete_doc("Email Queue", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Badge Assignment",
        filters={"member": ["like", f"{AUTOMATION_EMAIL_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Badge Assignment", name, force=True, ignore_permissions=True)

    live_classes = frappe.get_all(
        "LMS Live Class",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    )
    if live_classes:
        frappe.db.delete("LMS Live Class Participant", {"live_class": ["in", live_classes]})
        frappe.db.delete("LMS Live Class", {"name": ["in", live_classes]})

    for name in frappe.get_all(
        "LMS Badge",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Badge", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Program",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Program", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Batch",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        try:
            delete_batch(name)
        except Exception:
            frappe.delete_doc("LMS Batch", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Assignment Submission",
        filters={"member": ["like", f"{AUTOMATION_EMAIL_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Assignment Submission", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Assignment",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Assignment", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Quiz Submission",
        filters={"member": ["like", f"{AUTOMATION_EMAIL_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Quiz Submission", name, force=True, ignore_permissions=True)

    for name in frappe.get_all(
        "LMS Quiz",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("LMS Quiz", name, force=True, ignore_permissions=True)

    frappe.db.delete("LMS Question", {"question": ["like", f"{AUTOMATION_PREFIX}%"]})

    for name in frappe.get_all(
        "LMS Course",
        filters={"title": ["like", f"{AUTOMATION_PREFIX}%"]},
        pluck="name",
    ):
        try:
            delete_course(name)
        except Exception:
            frappe.delete_doc("LMS Course", name, force=True, ignore_permissions=True)

    for file_name in frappe.get_all(
        "File",
        filters={"file_name": ["like", "automation-%"]},
        pluck="name",
    ):
        frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)

    if frappe.db.exists("Email Account", OUTGOING_ACCOUNT_NAME):
        frappe.delete_doc("Email Account", OUTGOING_ACCOUNT_NAME, force=True, ignore_permissions=True)

    for email in frappe.get_all(
        "User",
        filters={"name": ["like", f"{AUTOMATION_EMAIL_PREFIX}%"]},
        pluck="name",
    ):
        frappe.delete_doc("User", email, force=True, ignore_permissions=True)


def ensure_outgoing_email_account() -> None:
    if frappe.db.exists("Email Account", OUTGOING_ACCOUNT_NAME):
        return

    doc = frappe.new_doc("Email Account")
    doc.name = OUTGOING_ACCOUNT_NAME
    doc.email_id = "automation@example.com"
    doc.email_account_name = "Automation Mailer"
    doc.enable_outgoing = 1
    doc.default_outgoing = 1
    doc.service = "Custom"
    doc.smtp_server = "localhost"
    doc.smtp_port = 25
    doc.auth_method = "Basic"
    doc.password = "dummy"
    doc.use_ssl = 0
    doc.use_starttls = 0
    doc.no_smtp_authentication = 1
    doc.db_insert()


def configure_lms_settings() -> None:
    settings = frappe.get_single("LMS Settings")
    settings.courses = 1
    settings.batches = 1
    settings.certifications = 1
    settings.jobs = 1
    settings.statistics = 1
    settings.notifications = 1
    settings.allow_guest_access = 1
    settings.save(ignore_permissions=True)


def create_public_file(file_name: str, content: bytes) -> str:
    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "content": content,
            "decode": False,
            "is_private": 0,
        }
    )
    file_doc.save(ignore_permissions=True)
    return file_doc.file_url


def create_users(avatar_url: str) -> dict[str, dict[str, str]]:
    specs = {
        "course_user": ("automation.student@example.com", "Course", "Student", ["LMS Student"], None),
        "free_enroll_user": ("automation.enroll@example.com", "Enroll", "Student", ["LMS Student"], None),
        "completed_user": ("automation.completed@example.com", "Completed", "Student", ["LMS Student"], None),
        "batch_user": ("automation.batch@example.com", "Batch", "Student", ["LMS Student"], None),
        "quiz_attempt_user": ("automation.quiz.attempt@example.com", "Quiz", "Attempt", ["LMS Student"], None),
        "quiz_timer_user": ("automation.quiz.timer@example.com", "Quiz", "Timer", ["LMS Student"], None),
        "quiz_single_user": ("automation.quiz.single@example.com", "Quiz", "Single", ["LMS Student"], None),
        "quiz_score_user": ("automation.quiz.score@example.com", "Quiz", "Score", ["LMS Student"], None),
        "quiz_show_answers_user": ("automation.quiz.answers@example.com", "Quiz", "Answers", ["LMS Student"], None),
        "quiz_max_user": ("automation.quiz.max@example.com", "Quiz", "Max", ["LMS Student"], None),
        "quiz_retake_user": ("automation.quiz.retake@example.com", "Quiz", "Retake", ["LMS Student"], None),
        "shuffle_user": ("automation.quiz.shuffle@example.com", "Quiz", "Shuffle", ["LMS Student"], None),
        "badge_user": ("automation.badge@example.com", "Badge", "Student", ["LMS Student"], None),
        "upgrade_user": ("automation.upgrade@example.com", "Upgrade", "Student", ["LMS Student"], None),
        "instructor": (
            "automation.instructor@example.com",
            "Automation",
            "Instructor",
            ["Moderator", "Course Creator", "Batch Evaluator"],
            avatar_url,
        ),
    }

    users: dict[str, dict[str, str]] = {
        "admin": {
            "email": "Administrator",
            "password": "admin",
            "username": "administrator",
        }
    }

    update_password("Administrator", "admin", logout_all_sessions=False)

    for key, (email, first_name, last_name, roles, user_image) in specs.items():
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.user_type = "Website User"
        user.enabled = 1
        user.send_welcome_email = 0
        if user_image:
            user.user_image = user_image
        for role in [role for role in roles if role != "LMS Student"]:
            user.append("roles", {"role": role})
        user.save(ignore_permissions=True)
        update_password(email, USER_PASSWORD, logout_all_sessions=False)
        if "Batch Evaluator" in roles and not frappe.db.exists("Course Evaluator", {"evaluator": email}):
            evaluator = frappe.new_doc("Course Evaluator")
            evaluator.evaluator = email
            evaluator.save(ignore_permissions=True)
        users[key] = {
            "email": email,
            "password": USER_PASSWORD,
            "username": frappe.db.get_value("User", email, "username") or "",
        }

    for index in range(1, 101):
        email = f"automation.analytics.{index:03d}@example.com"
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = "Analytics"
        user.last_name = f"User {index:03d}"
        user.user_type = "Website User"
        user.enabled = 1
        user.send_welcome_email = 0
        user.save(ignore_permissions=True)

    return users


def create_courses(instructor: dict[str, str], files: dict[str, str]) -> dict[str, dict[str, str]]:
    free_course = frappe.new_doc("LMS Course")
    free_course.update(
        {
            "title": "Automation Free Course",
            "short_introduction": "A deterministic course used for UI automation around lessons and certificates.",
            "description": "<p>Automation free course description.</p>",
            "category": "Business",
            "published": 1,
            "enable_certification": 1,
            "published_on": now(),
            "instructors": [{"instructor": instructor["email"]}],
        }
    )
    free_course.save(ignore_permissions=True)

    free_chapter = create_chapter(free_course.name, "Automation Fundamentals")
    video_lesson = create_lesson(
        free_course.name,
        free_chapter.name,
        "Automation Video Lesson",
        body='{{ YouTubeVideo("dQw4w9WgXcQ") }}',
    )
    formatted_lesson = create_lesson(
        free_course.name,
        free_chapter.name,
        "Automation Formatted Lesson",
        body=(
            "# Automation Formatting\n\n"
            "This lesson has **bold formatting** for the report.\n\n"
            "- first checklist item\n"
            "- second checklist item\n\n"
            "```python\nprint(\"AET TEAM\")\n```"
        ),
    )
    pdf_lesson = create_lesson(
        free_course.name,
        free_chapter.name,
        "Automation PDF Lesson",
        body=(
            "# Downloadable Guide\n\n"
            f"[Download Automation Guide]({files['guide_pdf_url']})"
        ),
    )

    agile_course = frappe.new_doc("LMS Course")
    agile_course.update(
        {
            "title": "Automation Agile Sprint Course",
            "short_introduction": "Agile course content for search validation.",
            "description": "<p>Agile course used by the automation search test.</p>",
            "category": "Business",
            "published": 1,
            "published_on": now(),
            "instructors": [{"instructor": instructor["email"]}],
        }
    )
    agile_course.save(ignore_permissions=True)

    paid_course = frappe.new_doc("LMS Course")
    paid_course.update(
        {
            "title": "Automation Paid Course",
            "short_introduction": "Paid course used to validate billing redirects.",
            "description": "<p>Paid course description for billing testing.</p>",
            "category": "Business",
            "published": 1,
            "published_on": now(),
            "paid_course": 1,
            "course_price": 199,
            "currency": "USD",
            "instructors": [{"instructor": instructor["email"]}],
        }
    )
    paid_course.save(ignore_permissions=True)

    draft_course = frappe.new_doc("LMS Course")
    draft_course.update(
        {
            "title": "Automation Draft Course",
            "short_introduction": "Draft course should stay hidden from students.",
            "description": "<p>Draft course description.</p>",
            "category": "Business",
            "published": 0,
            "instructors": [{"instructor": instructor["email"]}],
        }
    )
    draft_course.save(ignore_permissions=True)

    return {
        "free": {
            "name": free_course.name,
            "title": free_course.title,
            "video_route": "1-1",
            "formatted_route": "1-2",
            "pdf_route": "1-3",
            "video_lesson": video_lesson.name,
            "formatted_lesson": formatted_lesson.name,
            "pdf_lesson": pdf_lesson.name,
        },
        "agile": {"name": agile_course.name, "title": agile_course.title},
        "paid": {"name": paid_course.name, "title": paid_course.title},
        "draft": {"name": draft_course.name, "title": draft_course.title},
    }


def create_chapter(course_name: str, title: str):
    chapter = frappe.new_doc("Course Chapter")
    chapter.course = course_name
    chapter.title = title
    chapter.save(ignore_permissions=True)

    course = frappe.get_doc("LMS Course", course_name)
    course.append("chapters", {"chapter": chapter.name})
    course.save(ignore_permissions=True)
    return chapter


def create_lesson(course_name: str, chapter_name: str, title: str, body: str | None = None):
    lesson = frappe.new_doc("Course Lesson")
    lesson.course = course_name
    lesson.chapter = chapter_name
    lesson.title = title
    if body:
        lesson.body = body
    lesson.save(ignore_permissions=True)

    chapter = frappe.get_doc("Course Chapter", chapter_name)
    chapter.append("lessons", {"lesson": lesson.name})
    chapter.save(ignore_permissions=True)
    return lesson


def create_question(title: str, correct_option: str, wrong_option: str, explanation: str) -> str:
    question = frappe.new_doc("LMS Question")
    question.question = title
    question.type = "Choices"
    question.option_1 = correct_option
    question.is_correct_1 = 1
    question.option_2 = wrong_option
    question.is_correct_2 = 0
    question.explanation_1 = explanation
    question.explanation_2 = "This is not the correct answer."
    question.save(ignore_permissions=True)
    return question.name


def create_quizzes() -> dict[str, dict[str, Any]]:
    core_questions: list[dict[str, str]] = []
    for index in range(1, 6):
        correct = f"Correct Answer {index}"
        wrong = f"Wrong Answer {index}"
        question_name = create_question(
            f"Automation Core Question {index}",
            correct,
            wrong,
            f"Explanation for question {index}",
        )
        core_questions.append({"name": question_name, "correct": correct, "wrong": wrong})

    core_quiz = frappe.new_doc("LMS Quiz")
    core_quiz.update(
        {
            "title": "Automation Core Quiz",
            "passing_percentage": 60,
            "total_marks": 5,
            "max_attempts": 3,
            "show_answers": 1,
            "show_submission_history": 1,
            "duration": 1,
        }
    )
    for question in core_questions:
        core_quiz.append("questions", {"question": question["name"], "marks": 1})
    core_quiz.save(ignore_permissions=True)

    shuffle_questions: list[dict[str, str]] = []
    for index in range(1, 5):
        correct = f"Shuffle Correct {index}"
        wrong = f"Shuffle Wrong {index}"
        question_name = create_question(
            f"Automation Shuffle Question {index}",
            correct,
            wrong,
            f"Shuffle explanation {index}",
        )
        shuffle_questions.append({"name": question_name, "correct": correct, "wrong": wrong})

    shuffle_quiz = frappe.new_doc("LMS Quiz")
    shuffle_quiz.update(
        {
            "title": "Automation Shuffle Quiz",
            "passing_percentage": 60,
            "total_marks": 4,
            "show_answers": 1,
            "shuffle_questions": 1,
        }
    )
    for question in shuffle_questions:
        shuffle_quiz.append("questions", {"question": question["name"], "marks": 1})
    shuffle_quiz.save(ignore_permissions=True)

    badge_questions: list[dict[str, str]] = []
    for index in range(1, 4):
        correct = f"Badge Correct {index}"
        wrong = f"Badge Wrong {index}"
        question_name = create_question(
            f"Automation Badge Question {index}",
            correct,
            wrong,
            f"Badge explanation {index}",
        )
        badge_questions.append({"name": question_name, "correct": correct, "wrong": wrong})

    badge_quiz = frappe.new_doc("LMS Quiz")
    badge_quiz.update(
        {
            "title": "Automation Badge Quiz",
            "passing_percentage": 100,
            "total_marks": 3,
            "show_answers": 1,
        }
    )
    for question in badge_questions:
        badge_quiz.append("questions", {"question": question["name"], "marks": 1})
    badge_quiz.save(ignore_permissions=True)

    return {
        "core": {
            "name": core_quiz.name,
            "title": core_quiz.title,
            "questions": core_questions,
        },
        "shuffle": {
            "name": shuffle_quiz.name,
            "title": shuffle_quiz.title,
            "questions": shuffle_questions,
        },
        "badge": {
            "name": badge_quiz.name,
            "title": badge_quiz.title,
            "questions": badge_questions,
        },
    }


def create_assignment() -> dict[str, str]:
    assignment = frappe.new_doc("LMS Assignment")
    assignment.update(
        {
            "title": "Automation PDF Assignment",
            "type": "PDF",
            "grade_assignment": 1,
            "question": "<p>Upload your automation report as a PDF file.</p>",
        }
    )
    assignment.save(ignore_permissions=True)
    return {"name": assignment.name, "title": assignment.title}


def create_badges(badge_image_url: str) -> dict[str, str]:
    fast_learner = frappe.new_doc("LMS Badge")
    fast_learner.update(
        {
            "title": "Automation Fast Learner",
            "description": "Awarded when a learner completes the course.",
            "reference_doctype": "LMS Enrollment",
            "event": "Value Change",
            "image": badge_image_url,
            "grant_only_once": 1,
            "user_field": "member",
            "field_to_check": "progress",
            "condition": "doc.progress == 100",
        }
    )
    fast_learner.save(ignore_permissions=True)

    master_of_quiz = frappe.new_doc("LMS Badge")
    master_of_quiz.update(
        {
            "title": "Automation Master of Quiz",
            "description": "Awarded for a perfect quiz score.",
            "reference_doctype": "LMS Quiz Submission",
            "event": "New",
            "image": badge_image_url,
            "grant_only_once": 1,
            "user_field": "member",
            "condition": "doc.percentage == 100",
        }
    )
    master_of_quiz.save(ignore_permissions=True)

    return {
        "fast_learner": fast_learner.name,
        "master_of_quiz": master_of_quiz.name,
    }


def create_program(courses: dict[str, dict[str, str]]) -> dict[str, str]:
    program = frappe.new_doc("LMS Program")
    program.title = "Automation Program"
    program.published = 1
    program.enforce_course_order = 1
    program.append("program_courses", {"course": courses["free"]["name"]})
    program.append("program_courses", {"course": courses["agile"]["name"]})
    program.save(ignore_permissions=True)
    return {"name": program.name, "title": program.title}


def create_batch_and_live_classes(courses: dict[str, dict[str, str]], instructor: dict[str, str]):
    batch = frappe.new_doc("LMS Batch")
    batch.update(
        {
            "title": "Automation Live Batch",
            "published": 1,
            "allow_self_enrollment": 1,
            "start_date": nowdate(),
            "end_date": add_days(nowdate(), 7),
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "timezone": "Asia/Saigon",
            "description": "Automation batch description.",
            "batch_details": "<p>Automation batch details.</p>",
            "show_live_class": 1,
            "instructors": [{"instructor": instructor["email"]}],
            "courses": [{"course": courses["free"]["name"], "evaluator": instructor["email"]}],
        }
    )
    batch.save(ignore_permissions=True)

    today_class = create_live_class(
        title="Automation Live Class Today",
        batch_name=batch.name,
        host=instructor["email"],
        date_value=nowdate(),
        time_value="23:59:00",
        duration=30,
        join_url="https://example.com/automation-live-class",
    )
    future_class = create_live_class(
        title="Automation Live Class Future",
        batch_name=batch.name,
        host=instructor["email"],
        date_value=add_days(nowdate(), 1),
        time_value="10:00:00",
        duration=30,
        join_url="https://example.com/automation-live-class-future",
    )

    return {"name": batch.name, "title": batch.title}, {
        "today": today_class,
        "future": future_class,
    }


def create_live_class(
    title: str,
    batch_name: str,
    host: str,
    date_value: str,
    time_value: str,
    duration: int,
    join_url: str,
) -> dict[str, str]:
    doc = frappe.new_doc("LMS Live Class")
    doc.name = frappe.scrub(title)
    doc.title = title
    doc.host = host
    doc.batch_name = batch_name
    doc.date = date_value
    doc.time = time_value
    doc.duration = duration
    doc.timezone = "Asia/Saigon"
    doc.join_url = join_url
    doc.start_url = join_url
    doc.attendees = 1
    doc.owner = "Administrator"
    doc.modified_by = "Administrator"
    doc.creation = now()
    doc.modified = now()
    doc.db_insert()
    return {"name": doc.name, "title": title}


def create_course_enrollment(user: dict[str, str], course: dict[str, str]) -> None:
    enrollment = frappe.new_doc("LMS Enrollment")
    enrollment.member = user["email"]
    enrollment.course = course["name"]
    enrollment.insert(ignore_permissions=True)


def create_batch_enrollment(user: dict[str, str], batch: dict[str, str]) -> None:
    enrollment = frappe.new_doc("LMS Batch Enrollment")
    enrollment.member = user["email"]
    enrollment.batch = batch["name"]
    enrollment.confirmation_email_sent = 1
    enrollment.insert(ignore_permissions=True)


def complete_course_for_user(user_email: str, course: dict[str, str]) -> None:
    frappe.set_user(user_email)
    for lesson_name in (
        course["video_lesson"],
        course["formatted_lesson"],
        course["pdf_lesson"],
    ):
        save_progress(lesson_name, course["name"])
    frappe.set_user("Administrator")


def create_quiz_attempts(
    quizzes: dict[str, dict[str, Any]],
    users: dict[str, dict[str, str]],
    badges: dict[str, str],
) -> None:
    core_questions = quizzes["core"]["questions"]
    badge_questions = quizzes["badge"]["questions"]

    for _ in range(3):
        submit_choice_quiz(
            quizzes["core"]["name"],
            users["quiz_max_user"]["email"],
            core_questions,
            use_all_correct=False,
        )

    submit_choice_quiz(
        quizzes["badge"]["name"],
        users["badge_user"]["email"],
        badge_questions,
        use_all_correct=True,
    )


def submit_choice_quiz(
    quiz_name: str,
    user_email: str,
    questions: list[dict[str, str]],
    use_all_correct: bool,
) -> None:
    results = []
    for index, question in enumerate(questions):
        answer = question["correct"]
        if not use_all_correct and index == len(questions) - 1:
            answer = question["wrong"]
        results.append({"question_name": question["name"], "answer": [answer]})

    frappe.set_user(user_email)
    submit_quiz(quiz_name, json.dumps(results))
    frappe.set_user("Administrator")


def create_search_index() -> None:
    build_index()


if __name__ == "__main__":
    main()
