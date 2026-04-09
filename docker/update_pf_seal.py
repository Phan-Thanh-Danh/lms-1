"""
Frappe whitelisted script để cập nhật Print Format qua bench execute.
Chạy: bench --site lms.localhost execute workspace.update_pf_seal
"""
import frappe


def run(**kwargs):
    html_path = "/workspace/tmp_templates/lms_certificate_print_format.html"
    with open(html_path, "r", encoding="utf-8") as f:
        new_html = f.read()

    print(f"HTML length: {len(new_html)} chars")
    print(f"Has MOCCHUNGCHI: {'MOCCHUNGCHI' in new_html}")
    print(f"Has cert-stamp-img: {'cert-stamp-img' in new_html}")

    pf = frappe.get_doc("Print Format", "LMS Certificate Premium")
    pf.html = new_html
    pf.save(ignore_permissions=True)
    frappe.db.commit()
    print("SUCCESS: LMS Certificate Premium updated with MOCCHUNGCHI stamp")
    return "Done"
