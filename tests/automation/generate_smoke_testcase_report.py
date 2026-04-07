from __future__ import annotations

import csv
from datetime import date
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT_DIR / "tests" / "automation" / "reports"
JUNIT_PATH = REPORTS_DIR / "smoke_junit.xml"
CSV_PATH = REPORTS_DIR / "smoke_testcase_report.csv"
MD_PATH = REPORTS_DIR / "smoke_testcase_report.md"
HTML_PATH = REPORTS_DIR / "smoke_testcase_report.html"

TESTCASE_METADATA = {
    "test_tc01_login_redirects_to_dashboard": {
        "id": "TC01",
        "description": "Kiểm tra đăng nhập thành công và chuyển hướng về Dashboard.",
        "procedure": "Mở trang login, nhập Administrator/admin và nhấn Đăng nhập.",
        "expected": "URL chuyển hướng về trang /app hoặc /desk thành công.",
        "note": "Xác nhận khả năng truy cập cơ bản vào hệ thống.",
    },
    "test_tc21_enrolled_student_can_access_live_class_join_link": {
        "id": "TC21",
        "description": "Sinh viên đã đăng ký có thể truy cập link tham gia lớp học trực tuyến.",
        "procedure": "Đăng nhập sinh viên, mở tab Classes của Batch hiện tại.",
        "expected": "Nút 'Join' hiển thị và dẫn đến liên kết lớp học trực tuyến mẫu.",
        "note": "Xác nhận tính năng đào tạo trực tiếp (Live Class) hoạt động.",
    },
    "test_tc24_fast_learner_badge_is_assigned_on_course_completion": {
        "id": "TC24",
        "description": "Huy hiệu 'Fast Learner' được cấp khi hoàn thành khóa học nhanh.",
        "procedure": "Kiểm tra danh sách huy hiệu của sinh viên đã hoàn thành khóa học.",
        "expected": "Huy hiệu xuất hiện chính xác trong bộ sưu tập của người dùng.",
        "note": "Kiểm tra hệ thống cấp huy hiệu tự động (Gamification).",
    },
    "test_tc26_admin_can_create_user_and_queue_welcome_email": {
        "id": "TC26",
        "description": "Admin tạo người dùng mới và kiểm tra email chào mừng trong hàng chờ.",
        "procedure": "Tạo người dùng qua hệ thống và kiểm tra hàng chờ email (Email Queue).",
        "expected": "Email chào mừng được tạo thành công và nằm trong hàng chờ gửi đi.",
        "note": "Xác nhận tính năng quản trị người dùng và thông báo email.",
    },
    "test_tc28_statistics_page_reports_at_least_100_users": {
        "id": "TC28",
        "description": "Trang thống kê hiển thị báo cáo lượng người dùng chính xác.",
        "procedure": "Đăng nhập Admin, truy cập đường dẫn /lms/statistics.",
        "expected": "Biểu đồ và thẻ thông tin hiển thị tổng số lượng người dùng >= 100.",
        "note": "Kiểm tra tính năng báo cáo dữ liệu (Dashboard Statistics).",
    },
    "test_tc29_homepage_renders_cleanly_on_iphone_13_viewport": {
        "id": "TC29",
        "description": "Kiểm tra hiển thị giao diện trang chủ trên trình duyệt di động.",
        "procedure": "Đặt kích thước trình duyệt theo iPhone 13 (390x844) và tải trang chủ.",
        "expected": "Giao diện hiển thị sạch sẽ, không bị lỗi tràn khung hình ngang.",
        "note": "Xác nhận tính đáp ứng (Responsive) của trang chủ.",
    },
    "test_tc34_student_can_post_a_comment_in_batch_discussions": {
        "id": "TC34",
        "description": "Sinh viên có thể đăng bình luận trao đổi trong nhóm học (Batch).",
        "procedure": "Đăng nhập sinh viên, mở phần Thảo luận và đăng một nội dung mới.",
        "expected": "Nội dung vừa đăng hiển thị ngay lập tức trong luồng thảo luận.",
        "note": "Kiểm tra tính năng tương tác xã hội trong học tập.",
    },
    "test_tc53_sidebar_navigation_opens_core_lms_sections": {
        "id": "TC53",
        "description": "Kiểm tra khả năng điều hướng các mục chính từ sidebar.",
        "procedure": "Nhấn lần lượt vào các biểu tượng Courses, Batches, Statistics trên sidebar.",
        "expected": "Hệ thống chuyển đổi trang mượt mà và hiển thị đúng nội dung tương ứng.",
        "note": "Xác nhận luồng điều hướng tổng thể của ứng dụng.",
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
        "# Báo cáo kết quả kiểm thử Smoke Suite",
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
  <title>Báo cáo kiểm thử Smoke Suite</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 24px; color: #1f2937; line-height: 1.5; }}
    h1 {{ margin-bottom: 16px; color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ border: 1px solid #cbd5e1; padding: 12px; vertical-align: top; text-align: left; }}
    th {{ background: #1e40af; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; }}
    tr:nth-child(even) {{ background: #f8fafc; }}
    tr:hover {{ background: #f1f5f9; }}
  </style>
</head>
<body>
  <h1>Báo cáo kết quả kiểm thử Smoke Suite</h1>
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
