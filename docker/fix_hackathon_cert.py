import frappe
import base64

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()

    print("--- SỬA LANDSCAPE + FULL A4 ---")

    fmt_name = "Cert_Fmt_Hackathon"

    phoi_path = "/workspace/lms/public/images/phoi.jpg"
    with open(phoi_path, "rb") as f:
        phoi_b64 = base64.b64encode(f.read()).decode('utf-8')
    phoi_data_uri = f"data:image/jpeg;base64,{phoi_b64}"

    # HTML tối giản nhất cho wkhtmltopdf landscape
    # Không dùng mm/cm vì wkhtmltopdf landscape = 842x595px (96dpi)
    # Dùng 100vw/100vh để đảm bảo luôn phủ full trang
    hack_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  @page {{ size: A4 landscape; margin: 0; }}

  /* Lệnh Tối Mật của Frappe để báo cho wkhtmltopdf biết là Landscape */
  .print-format {{
     orientation: Landscape;
     page-size: A4;
     margin-top: 0mm;
     margin-bottom: 0mm;
     margin-left: 0mm;
     margin-right: 0mm;
  }}

  html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    font-family: Arial, sans-serif;
  }}

  .page {{
    position: relative;
    width: 297mm;
    height: 210mm;
  }}

  .page img.bg {{
    position: absolute;
    top: 0; left: 0;
    width: 297mm;
    height: 210mm;
    display: block;
    object-fit: fill;
  }}

  .overlay {{
    position: absolute;
    top: 0; left: 0;
    width: 297mm;
    height: 210mm;
  }}

  /* === CHỈNH TỌA ĐỘ THEO mm ĐỂ FIX LỖI BỐ CỤC WKHTMLTOPDF === */

  .f-name {{
    position: absolute;
    left: 0; width: 297mm;
    top: 85mm;
    text-align: center;
    font-size: 45px;
    font-weight: 900;
    color: #1a1a1a;
    text-transform: uppercase;
    letter-spacing: 2px;
  }}

  .f-course {{
    position: absolute;
    left: 0; width: 297mm;
    top: 115mm;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    color: #333;
  }}

  .f-score {{
    position: absolute;
    left: 0; width: 297mm;
    top: 135mm;
    text-align: center;
    font-size: 20px;
    color: #555;
  }}

  .f-date {{
    position: absolute;
    left: 65mm;
    top: 165mm;
    text-align: center;
    width: 60mm;
    font-size: 18px;
    color: #111;
  }}

  .f-sig {{
    position: absolute;
    right: 65mm;
    top: 165mm;
    text-align: center;
    width: 60mm;
    font-size: 20px;
    font-weight: bold;
    font-style: italic;
    color: #111;
  }}

  .f-seal {{
    position: absolute;
    right: 48mm;
    top: 172mm;
    width: 23mm;
    height: 23mm;
    opacity: 0.95;
    transform: rotate(-8deg);
    mix-blend-mode: multiply;
    filter: drop-shadow(0 1px 3px rgba(0,0,0,0.1));
    z-index: 10;
    pointer-events: none;
  }}
</style>
</head>
<body>
<div class="page">
  <img class="bg" src="{phoi_data_uri}" alt=""/>
  <div class="overlay">
    <div class="f-name">{{{{ doc.member_name or doc.full_name }}}}</div>
    <div class="f-course">{{{{ doc.course_title or doc.course }}}}</div>
    <div class="f-score">Điểm: {{{{ doc.score or '100' }}}} / 100</div>
    <div class="f-date">{{{{ frappe.utils.formatdate(doc.issue_date) }}}}</div>
    <div class="f-sig">{{{{ doc.evaluator_name or '' }}}}</div>
    <img class="f-seal" src="/assets/lms/images/MOCCHUNGCHI.png" alt="Seal"/>
  </div>
</div>
</body>
</html>"""

    fmt = frappe.get_doc("Print Format", fmt_name)
    fmt.html = hack_html
    fmt.margin_top = 0
    fmt.margin_bottom = 0
    fmt.margin_left = 0
    fmt.margin_right = 0
    fmt.page_number = "Hide"
    # Set orientation = landscape qua trường Frappe (quan trọng!)
    fmt.orientation = "Landscape"
    fmt.save(ignore_permissions=True)

    frappe.db.commit()
    print("--- HOÀN TẤT ---")
    print("PDF link: http://localhost:8000/api/method/frappe.utils.print_format.download_pdf?doctype=LMS+Certificate&name=euc10e8igq&format=Cert_Fmt_Hackathon")

if __name__ == "__main__":
    run()
