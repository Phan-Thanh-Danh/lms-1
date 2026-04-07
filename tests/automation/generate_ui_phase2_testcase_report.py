from __future__ import annotations

import csv
from datetime import date
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT_DIR / "tests" / "automation" / "reports"
JUNIT_PATH = REPORTS_DIR / "ui_phase2_junit.xml"
CSV_PATH = REPORTS_DIR / "ui_phase2_testcase_report.csv"
MD_PATH = REPORTS_DIR / "ui_phase2_testcase_report.md"
HTML_PATH = REPORTS_DIR / "ui_phase2_testcase_report.html"

TESTCASE_METADATA = {
    "test_ui21_student_can_enroll_in_free_course": {
        "id": "UI21",
        "description": "Học viên có thể đăng ký vào khóa học miễn phí từ giao diện chi tiết khóa học.",
        "procedure": "Đăng nhập bằng tài khoản học viên chưa đăng ký. Mở trang chi tiết khóa học miễn phí và nhấn Start Learning.",
        "expected": "Hệ thống tạo đăng ký (enrollment) thành công và điều hướng học viên vào bài học đầu tiên.",
        "note": "Luồng đăng ký có tác động đến dữ liệu thành viên, phù hợp kiểm thử ở Phase 2.",
    },
    "test_ui22_lesson_page_auto_updates_progress_for_enrolled_student": {
        "id": "UI22",
        "description": "Trang bài học tự động cập nhật tiến độ khi học viên mở bài học chưa hoàn thành.",
        "procedure": "Reset tiến độ về 0, đăng nhập học viên đã đăng ký, mở một bài học bất kỳ.",
        "expected": "Tiến độ hiển thị trên giao diện lớn hơn 0% và trường progress trong hệ thống được cập nhật.",
        "note": "Xác nhận logic tự động cập nhật tiến độ (Auto-update progress) của hệ thống.",
    },
    "test_ui23_completed_student_sees_certificate_button": {
        "id": "UI23",
        "description": "Học viên đã hoàn thành khóa học nhìn thấy nút Get Certificate.",
        "procedure": "Đăng nhập bằng tài khoản đã hoàn thành toàn bộ bài học và mở trang chi tiết khóa học đó.",
        "expected": "Trang chi tiết khóa học hiển thị nút Get Certificate để học viên nhận chứng chỉ.",
        "note": "Xác nhận trạng thái hoàn thành (Completion state) đã được giao diện nhận diện đúng.",
    },
    "test_ui24_notification_list_shows_backend_created_unread_item": {
        "id": "UI24",
        "description": "Trang Thông báo hiển thị đúng dữ liệu thông báo chưa đọc được tạo từ hệ thống.",
        "procedure": "Tạo một thông báo chưa đọc cho học viên, đăng nhập và kiểm tra trang Notifications.",
        "expected": "Danh sách Unread hiển thị đúng tiêu đề và nội dung thông báo vừa tạo.",
        "note": "Kiểm tra tính đồng bộ nội dung thông báo giữa Backend và Frontend.",
    },
    "test_ui25_notification_can_move_from_unread_to_read": {
        "id": "UI25",
        "description": "Người dùng có thể đánh dấu thông báo là đã đọc trên giao diện.",
        "procedure": "Mở trang Notifications, nhấn nút đánh dấu đã đọc trên một thông báo, sau đó kiểm tra tab Read.",
        "expected": "Thông báo biến mất khỏi tab Unread và xuất hiện chính xác ở tab Read.",
        "note": "Kiểm tra tương tác người dùng và thay đổi trạng thái thông báo.",
    },
    "test_ui26_quiz_first_attempt_is_recorded": {
        "id": "UI26",
        "description": "Lần làm Quiz đầu tiên được ghi nhận thành công vào hệ thống.",
        "procedure": "Đăng nhập, mở một bài Quiz, trả lời các câu hỏi và nhấn nộp bài.",
        "expected": "Hệ thống hiển thị bảng tổng kết (Quiz Summary) và ghi lại 1 lần nộp bài (Submission).",
        "note": "Quy trình quan trọng nhất trong việc đánh giá kết quả học tập.",
    },
    "test_ui27_quiz_blocks_after_maximum_attempts": {
        "id": "UI27",
        "description": "Hệ thống chặn học viên làm Quiz khi đã đạt tối đa số lần thử cho phép.",
        "procedure": "Sử dụng tài khoản đã làm đủ 3 lần, mở bài Quiz yêu cầu tối đa 3 lần làm bài.",
        "expected": "Trang Quiz hiển thị thông báo đã hết lượt làm bài và không hiển thị nút bắt đầu.",
        "note": "Xác nhận tính năng giới hạn lượt làm bài (Attempt limits) hoạt động đúng.",
    },
    "test_ui28_quiz_score_summary_shows_eighty_percent": {
        "id": "UI28",
        "description": "Bảng tổng kết Quiz hiển thị đúng tỷ lệ 80% khi làm đúng 4/5 câu.",
        "procedure": "Thực hiện làm Quiz với 4 câu trả lời đúng và 1 câu trả lời sai, sau đó nộp bài.",
        "expected": "Trang kết quả hiển thị thông điệp 'You got 80% correct answers'.",
        "note": "Xác nhận thuật toán tính điểm và hiển thị kết quả trên giao diện.",
    },
    "test_ui29_assignment_accepts_pdf_upload": {
        "id": "UI29",
        "description": "Giao diện nộp bài tập (Assignment) chấp nhận tệp PDF hợp lệ.",
        "procedure": "Đăng nhập học viên, mở trang nộp bài tập, tải lên một tệp PDF và nhấn Save.",
        "expected": "Tệp được tải lên thành công và hệ thống tạo một bản ghi nộp bài tập mới.",
        "note": "Kiểm tra tính năng lưu trữ và quản lý tệp tin nộp bài của sinh viên.",
    },
    "test_ui30_assignment_rejects_exe_upload": {
        "id": "UI30",
        "description": "Giao diện nộp bài tập từ chối tệp tin không hợp lệ (ví dụ: .EXE).",
        "procedure": "Thực hiện tải lên một tệp có đuôi .EXE vào form nộp bài tập.",
        "expected": "Hệ thống hiển thị thông báo lỗi 'Only PDF files are allowed' và từ chối lưu bài.",
        "note": "Kiểm tra tính năng bảo mật và ràng buộc định dạng tệp tin tải lên.",
    },
}


def parse_junit_results() -> dict[str, tuple[str, str]]:
    results: dict[str, tuple[str, str]] = {}
    if not JUNIT_PATH.exists():
        return results

    root = ET.parse(JUNIT_PATH).getroot()
    for testcase in root.iter("testcase"):
        name = testcase.get("name")
        if not name:
            continue

        result = "Passed"
        details = ""

        failure = testcase.find("failure")
        error = testcase.find("error")
        skipped = testcase.find("skipped")

        if failure is not None:
            result = "Failed"
            details = (failure.get("message") or failure.text or "").strip().splitlines()[0]
        elif error is not None:
            result = "Error"
            details = (error.get("message") or error.text or "").strip().splitlines()[0]
        elif skipped is not None:
            result = "Skipped"
            details = (skipped.get("message") or skipped.text or "").strip().splitlines()[0]

        results[name] = (result, details)

    return results


def build_rows() -> list[dict[str, str]]:
    test_date = date.today().isoformat()
    junit_results = parse_junit_results()
    rows: list[dict[str, str]] = []

    for test_name, meta in TESTCASE_METADATA.items():
        result_status, details = junit_results.get(test_name, ("Not Run", "Không tìm thấy kết quả trong file junit."))
        
        # Translate result status
        result_map = {
            "Passed": "Đạt (Passed)",
            "Failed": "Không đạt (Failed)",
            "Error": "Lỗi (Error)",
            "Skipped": "Bỏ qua (Skipped)",
            "Not Run": "Chưa chạy"
        }
        result = result_map.get(result_status, result_status)
        
        note = meta["note"]
        if details and result_status not in {"Passed", "Not Run"}:
            note = f"{note} Chi tiết lỗi: {details}"

    # Re-using the headers from reports
        rows.append(
            {
                "ID": meta["id"],
                "Test Case Description": meta["description"],
                "Test Case Procedure": meta["procedure"],
                "Expected Output": meta["expected"],
                "Test date": test_date,
                "Result": result,
                "Note": note,
            }
        )

    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "ID",
                "Test Case Description",
                "Test Case Procedure",
                "Expected Output",
                "Test date",
                "Result",
                "Note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines = [
        "# Báo cáo kết quả kiểm thử UI Phase 2",
        "",
        "| ID | Mô tả Test Case | Quy trình thực hiện | Kết quả mong đợi | Ngày chạy | Kết quả | Ghi chú |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {ID} | {desc} | {proc} | {exp} | {date} | {result} | {note} |".format(
                ID=row["ID"],
                desc=row["Test Case Description"].replace("|", "\\|"),
                proc=row["Test Case Procedure"].replace("|", "\\|"),
                exp=row["Expected Output"].replace("|", "\\|"),
                date=row["Test date"],
                result=row["Result"],
                note=row["Note"].replace("|", "\\|"),
            )
        )
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(rows: list[dict[str, str]]) -> None:
    headers = [
        "ID",
        "Mô tả Test Case",
        "Quy trình thực hiện",
        "Kết quả mong đợi",
        "Ngày chạy",
        "Kết quả",
        "Ghi chú",
    ]
    # Mapping for internal row keys to header labels
    row_keys = ["ID", "Test Case Description", "Test Case Procedure", "Expected Output", "Test date", "Result", "Note"]
    
    thead = "".join(f"<th>{escape(header)}</th>" for header in headers)
    tbody = []
    for row in rows:
        cells = "".join(f"<td>{escape(row[key])}</td>" for key in row_keys)
        tbody.append(f"<tr>{cells}</tr>")

    html = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Báo cáo kiểm thử UI Phase 2</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 24px; color: #1f2937; line-height: 1.5; }}
    h1 {{ margin-bottom: 16px; color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ border: 1px solid #cbd5e1; padding: 12px; vertical-align: top; text-align: left; }}
    th {{ background: #1e40af; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    tr:hover {{ background: #f1f5f9; }}
    .status-passed {{ color: #166534; font-weight: bold; }}
    .status-failed {{ color: #991b1b; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Báo cáo kết quả kiểm thử UI Phase 2</h1>
  <table>
    <thead><tr>{thead}</tr></thead>
    <tbody>
      {''.join(tbody)}
    </tbody>
  </table>
</body>
</html>
"""
    HTML_PATH.write_text(html, encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    write_html(rows)


if __name__ == "__main__":
    main()
