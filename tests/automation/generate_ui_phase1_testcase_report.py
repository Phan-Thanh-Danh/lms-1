from __future__ import annotations

import csv
from datetime import date
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT_DIR / "tests" / "automation" / "reports"
JUNIT_PATH = REPORTS_DIR / "ui_phase1_junit.xml"
CSV_PATH = REPORTS_DIR / "ui_phase1_testcase_report.csv"
MD_PATH = REPORTS_DIR / "ui_phase1_testcase_report.md"
HTML_PATH = REPORTS_DIR / "ui_phase1_testcase_report.html"

TESTCASE_METADATA = {
    "test_ui01_login_page_renders_core_controls": {
        "id": "UI01",
        "description": "Trang đăng nhập hiển thị đầy đủ các điều kỉển cơ bản.",
        "procedure": "Mở trang login. Kiểm tra ô Email, ô Password và nút Login xuất hiện.",
        "expected": "Trang login tải thành công và người dùng nhìn thấy đủ 3 thành phần chính để đăng nhập.",
        "note": "Kiểm tra nền tảng trang đăng nhập, không phụ thuộc dữ liệu nghiệp vụ.",
    },
    "test_ui02_admin_can_enter_lms_and_see_core_sidebar": {
        "id": "UI02",
        "description": "Admin đăng nhập vào LMS và thấy thanh điều hướng chính.",
        "procedure": "Đăng nhập bằng tài khoản Administrator/admin rồi mở giao diện LMS.",
        "expected": "Sidebar hiển thị các mục Home, Search, Notifications, Courses, Programs, Batches và Statistics.",
        "note": "Xác nhận phiên đăng nhập và bố cục chính của LMS hoạt động bình thường.",
    },
    "test_ui03_sidebar_opens_courses_page": {
        "id": "UI03",
        "description": "Từ sidebar có thể mở trang danh sách khóa học (Courses).",
        "procedure": "Nhấn vào menu Courses trên thanh điều hướng bên trái.",
        "expected": "URL chuyển sang /lms/courses và nội dung trang Courses hiển thị đầy đủ.",
        "note": "Luồng điều hướng cơ bản, độc lập với dữ liệu khóa học thực tế.",
    },
    "test_ui04_sidebar_opens_programs_page": {
        "id": "UI04",
        "description": "Từ sidebar có thể mở trang danh sách chương trình (Programs).",
        "procedure": "Nhấn vào menu Programs trên thanh điều hướng bên trái.",
        "expected": "URL chuyển sang /lms/programs, nút New hiển thị và trang hiển thị danh sách hoặc trạng thái trống.",
        "note": "Xác nhận điều hướng và hiển thị phần đầu (header) của module Chương trình.",
    },
    "test_ui05_sidebar_opens_batches_page": {
        "id": "UI05",
        "description": "Từ sidebar có thể mở trang quản lý nhóm học (Batches).",
        "procedure": "Nhấn vào menu Batches trên thanh điều hướng bên trái.",
        "expected": "URL chuyển sang /lms/batches và tiêu đề 'All Batches' hiển thị rõ ràng.",
        "note": "Xác nhận điều hướng cơ bản cho module Batches.",
    },
    "test_ui06_sidebar_opens_search_page": {
        "id": "UI06",
        "description": "Trang tìm kiếm (Search) hiển thị ô nhập và hướng dẫn thao tác.",
        "procedure": "Mở trang Search, nhập một từ khóa bất kỳ vào ô tìm kiếm.",
        "expected": "Ô tìm kiếm giữ đúng giá trị đã nhập và giao diện hiển thị nhắc người dùng 'Press enter to search'.",
        "note": "Kiểm tra giao diện ô nhập liệu; kết quả tìm kiếm chi tiết sẽ được xử lý ở Phase 2.",
    },
    "test_ui07_sidebar_opens_notifications_page": {
        "id": "UI07",
        "description": "Từ sidebar có thể mở trang thông báo (Notifications).",
        "procedure": "Nhấn vào menu Notifications trên thanh điều hướng bên trái.",
        "expected": "Trang Notifications hiển thị đầy đủ hai tab 'Unread' và 'Read'.",
        "note": "Kiểm tra bố cục trang và các tab điều hướng thông báo.",
    },
    "test_ui08_sidebar_opens_statistics_page": {
        "id": "UI08",
        "description": "Từ sidebar có thể mở trang thống kê (Statistics).",
        "procedure": "Nhấn vào menu Statistics trên thanh điều hướng bên trái.",
        "expected": "Trang Statistics hiển thị được các thẻ chính như 'Signups' và 'Enrollments'.",
        "note": "Kiểm tra khả năng hiển thị biểu đồ và số liệu thống kê cơ bản.",
    },
    "test_ui09_user_menu_can_toggle_theme": {
        "id": "UI09",
        "description": "Người dùng có thể thay đổi giao diện Sáng/Tối (Light/Dark) từ menu cá nhân.",
        "procedure": "Mở menu người dùng ở góc trên cùng và chọn 'Toggle Theme'.",
        "expected": "Thuộc tính theme của trang thay đổi chính xác giữa chế độ sáng và tối.",
        "note": "Xác nhận tính năng cá nhân hóa giao diện hoạt động bình thường.",
    },
    "test_ui10_user_can_log_out_from_user_menu": {
        "id": "UI10",
        "description": "Người dùng có thể đăng xuất an toàn từ menu cá nhân.",
        "procedure": "Mở menu người dùng và chọn 'Log out'.",
        "expected": "Người dùng được đăng xuất và giao diện quay về trạng thái công khai (Guest).",
        "note": "Kiểm tra tính năng kết thúc phiên đăng nhập của người dùng.",
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
        "# Báo cáo kết quả kiểm thử UI Phase 1",
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
  <title>Báo cáo kiểm thử UI Phase 1</title>
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
  <h1>Báo cáo kết quả kiểm thử UI Phase 1</h1>
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
