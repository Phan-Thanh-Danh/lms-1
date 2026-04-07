from __future__ import annotations

import csv
from datetime import date
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT_DIR / "tests" / "automation" / "reports"
JUNIT_PATH = REPORTS_DIR / "quick_junit.xml"
CSV_PATH = REPORTS_DIR / "quick_testcase_report.csv"
MD_PATH = REPORTS_DIR / "quick_testcase_report.md"
HTML_PATH = REPORTS_DIR / "quick_testcase_report.html"

TESTCASE_METADATA = {
    "test_tc01_login_redirects_to_dashboard": {
        "id": "TC01",
        "description": "Kiểm tra đăng nhập thành công và chuyển hướng về Dashboard.",
        "procedure": "Mở trang login, nhập Administrator/admin và nhấn Đăng nhập.",
        "expected": "URL chuyển hướng về trang /app hoặc /desk và không còn ở trang login.",
        "note": "Test Case cơ bản nhất để xác nhận hệ thống đang chạy.",
    },
    "test_tc26_admin_can_create_user_and_queue_welcome_email": {
        "id": "TC26",
        "description": "Admin tạo người dùng mới và kiểm tra email chào mừng.",
        "procedure": "Sử dụng backend script để tạo User và kiểm tra Email Queue.",
        "expected": "Email chào mừng được tạo thành công trong hàng chờ (Email Queue).",
        "note": "Xác nhận tính năng tạo người dùng và hệ thống email hoạt động.",
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
        "# Báo cáo kết quả kiểm thử Quick Suite",
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
  <title>Báo cáo kiểm thử Quick Suite</title>
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
  <h1>Báo cáo kết quả kiểm thử Quick Suite</h1>
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
