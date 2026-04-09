#!/usr/bin/env python3
"""
update_stamp_seal.py
─────────────────────────────────────────────────────────────────────
Cập nhật Print Format "LMS Certificate Premium" trong Frappe DB
với ảnh mộc MOCCHUNGCHI.png + CSS effects.

Chạy: bench --site lms.localhost execute docker.update_stamp_seal.run
hoặc: docker exec lms-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site lms.localhost execute /workspace/update_stamp_seal.py"
"""

import frappe

# ─────────────────────────────────────────────────────────────────────────────
# Đọc HTML mới từ file local (đã được mount vào container qua volume /workspace)
# ─────────────────────────────────────────────────────────────────────────────
HTML_FILE = "/workspace/../lms/lms/doctype/lms_certificate/lms_certificate_print_format.html"

import os

def run():
    html_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "lms", "lms", "doctype", "lms_certificate", "lms_certificate_print_format.html"
    )
    html_path = os.path.normpath(html_path)

    if not os.path.exists(html_path):
        # Thử đường dẫn workspace
        html_path = "/workspace/lms/lms/doctype/lms_certificate/lms_certificate_print_format.html"

    print(f"📄 Đọc HTML từ: {html_path}")
    with open(html_path, "r", encoding="utf-8") as f:
        new_html = f.read()

    print(f"✅ Đọc thành công: {len(new_html)} ký tự")

    # Cập nhật "LMS Certificate Premium"
    target_formats = ["LMS Certificate Premium"]

    for pf_name in target_formats:
        try:
            pf = frappe.get_doc("Print Format", pf_name)
            pf.html = new_html
            pf.save(ignore_permissions=True)
            print(f"✅ Đã cập nhật Print Format: '{pf_name}'")
        except frappe.DoesNotExistError:
            print(f"⚠️  Không tìm thấy Print Format: '{pf_name}' — bỏ qua")
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật '{pf_name}': {e}")

    frappe.db.commit()
    print("\n🎉 Hoàn tất! Mộc chứng chỉ đã được cập nhật.")
    print("   🔗 URL ảnh mộc:  http://localhost:8000/files/MOCCHUNGCHI.png")
    print("   📐 CSS effects: rotate(-8deg), drop-shadow, opacity 0.88")
    print("   🔄 Dynamic seal: {{ doc.seal_image }} nếu có trường riêng")

if __name__ == "__main__":
    run()
