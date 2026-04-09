import frappe
import base64

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()
    
    # 1. Image Data
    phoi_path = "/workspace/phoi.jpg"
    with open(phoi_path, "rb") as f:
        phoi_b64 = base64.b64encode(f.read()).decode('utf-8')
    phoi_data_uri = f"data:image/jpeg;base64,{phoi_b64}"

    # 2. Hackathon HTML
    hack_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  @page {{ size: landscape; margin: 0; }}
  html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; background: #000; overflow: hidden; font-family: Arial, sans-serif; }}
  .page-container {{ position: relative; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; background: #fff; overflow: hidden; }}
  img.bg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; z-index: 1; }}
  .overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; }}
  .f-name {{ position: absolute; left: 5%; right: 5%; top: 38%; text-align: center; font-size: 38pt; font-weight: 900; color: #1a1a1a; text-transform: uppercase; }}
  .f-course {{ position: absolute; left: 5%; right: 5%; top: 54%; text-align: center; font-size: 22pt; font-weight: bold; color: #333; }}
  .f-score {{ position: absolute; left: 5%; right: 5%; top: 64%; text-align: center; font-size: 16pt; color: #444; }}
  .f-date {{ position: absolute; left: 15%; top: 78%; text-align: center; width: 25%; font-size: 14pt; color: #111; }}
  .f-sig {{ position: absolute; right: 15%; top: 78%; text-align: center; width: 30%; font-size: 16pt; font-weight: bold; font-style: italic; color: #111; }}
  .f-seal {{ position: absolute; right: 18%; top: 76%; width: 90pt; height: 90pt; opacity: 0.95; transform: rotate(-10deg); mix-blend-mode: multiply; z-index: 10; }}
</style>
</head>
<body>
<div class="page-container">
  <img class="bg" src="{phoi_data_uri}" alt=""/>
  <div class="overlay">
    <div class="f-name">{{{{ doc.member_name or 'Học Viên' }}}}</div>
    <div class="f-course">{{{{ doc.course_title or doc.course }}}}</div>
    <div class="f-score">Điểm: 100 / 100</div>
    <div class="f-date">{{{{ frappe.utils.formatdate(doc.issue_date) }}}}</div>
    <div class="f-sig">Lê Minh Trí</div>
    <img class="f-seal" src="/assets/lms/images/MOCCHUNGCHI.png" alt="Seal"/>
  </div>
</div>
</body>
</html>"""

    # 3. Premium HTML (Read from disk)
    premium_html_path = "/workspace/tmp_templates/lms_certificate_print_format.html"
    with open(premium_html_path, "r") as f:
        premium_html = f.read()

    # 4. Update Database
    if frappe.db.exists("Print Format", "Cert_Fmt_Hackathon"):
        frappe.db.set_value("Print Format", "Cert_Fmt_Hackathon", "html", hack_html)
    
    if frappe.db.exists("Print Format", "LMS Certificate Premium"):
        frappe.db.set_value("Print Format", "LMS Certificate Premium", "html", premium_html)

    frappe.db.commit()
    print("✅ DATABASE SYNC COMPLETE (HACKATHON & PREMIUM)")
    frappe.destroy()

if __name__ == "__main__":
    run()
