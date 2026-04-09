import frappe

def fix_all():
    frappe.init(site="lms.localhost")
    frappe.connect()

    # Tìm tất cả các Print Format bắt đầu bằng Cert_Fmt_
    formats = frappe.get_all("Print Format", filters={"name": ("like", "Cert_Fmt_%")})
    
    for f in formats:
        doc = frappe.get_doc("Print Format", f.name)
        
        # Reset các biến môi trường của Frappe Document (để tránh lỗi thụt lề 15mm mặc định)
        doc.margin_top = 0
        doc.margin_bottom = 0
        doc.margin_left = 0
        doc.margin_right = 0
        doc.page_number = "Hide"
        
        html = doc.html or ""
        
        # Tiêm mã ĐỘC QUYỀN ép Landscape thông qua cssutils của Frappe vào HTML
        if ".print-format {" not in html and "<style>" in html:
            magic_css = """
    /* Vượt mặt wkhtmltopdf: Bắt ép xoay ngang */
    .print-format {
        orientation: Landscape;
        page-size: A4;
        margin-top: 0mm;
        margin-bottom: 0mm;
        margin-left: 0mm;
        margin-right: 0mm;
    }
"""
            html = html.replace("<style>", f"<style>\n{magic_css}")
            doc.html = html
            
        doc.save(ignore_permissions=True)
        print(f"Đã Fix: {f.name} -> Ngang A4 Full Viền")
        
    frappe.db.commit()
    print("--- HOÀN TẤT FIX CÁC CHỨNG CHỈ ---")

if __name__ == "__main__":
    fix_all()
