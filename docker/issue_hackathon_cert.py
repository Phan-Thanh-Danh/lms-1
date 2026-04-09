import frappe
from frappe.utils import nowdate
import base64
import os

def run():
    # 1. SETUP PRINT FORMAT
    fmt_name = "Cert_Fmt_Hackathon"
    phoi_path = "/workspace/phoi.jpg"
    seal_path = "/workspace/MOCCHUNGCHI.png"
    
    # Base64 Background
    with open(phoi_path, "rb") as f:
        phoi_b64 = base64.b64encode(f.read()).decode('utf-8')
    phoi_data_uri = f"data:image/jpeg;base64,{phoi_b64}"

    # Base64 Seal
    with open(seal_path, "rb") as f:
        seal_b64 = base64.b64encode(f.read()).decode('utf-8')
    seal_data_uri = f"data:image/png;base64,{seal_b64}"

    hack_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  @page {{
    size: A4 portrait;
    margin: 0;
  }}

  html, body {{
    width: 210mm;
    background: #ffffff;
    font-family: Arial, sans-serif;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  /* Centering Wrapper */
  .certificate-page {{
    width: 210mm;
    height: 297mm;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }}

  /* 16:9 Inner Container */
  .certificate-inner {{
    position: relative;
    width: 210mm;
    height: 118.1mm; /* Exact 16:9 aspect ratio for 210mm width */
    overflow: hidden;
    background: #fff;
  }}

  img.bg {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: fill;
    z-index: 1;
  }}

  .content-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
  }}

  .f-name {{
    position: absolute;
    top: 40%;
    left: 0;
    width: 100%;
    text-align: center;
    font-size: 28pt;
    font-weight: bold;
    color: #1a1a1a;
    text-transform: uppercase;
  }}

  .f-course {{
    position: absolute;
    top: 55%;
    left: 0;
    width: 100%;
    text-align: center;
    font-size: 16pt;
    font-weight: bold;
    color: #333;
  }}

  .f-score {{
    position: absolute;
    top: 65%;
    left: 0;
    width: 100%;
    text-align: center;
    font-size: 12pt;
    color: #555;
  }}

  .f-date {{
    position: absolute;
    top: 80%;
    left: 15%;
    width: 30%;
    text-align: center;
    font-size: 10pt;
    color: #000;
  }}

  .f-sig {{
    position: absolute;
    top: 80%;
    right: 15%;
    width: 35%;
    text-align: center;
    font-size: 11pt;
    font-weight: bold;
    font-style: italic;
    color: #000;
  }}

  .f-seal {{
    position: absolute;
    top: 78%;
    right: 20%;
    width: 60pt;
    height: 60pt;
    opacity: 0.95;
    transform: rotate(-10deg);
    mix-blend-mode: multiply;
  }}
</style>
</head>
<body>
<div class="certificate-page">
  <div class="certificate-inner">
    <img class="bg" src="{phoi_data_uri}" alt=""/>
    <div class="content-overlay">
      <div class="f-name">{{{{ doc.member_name or 'Học Viên' }}}}</div>
      <div class="f-course">{{{{ doc.course_title or doc.course }}}}</div>
      <div class="f-score">Điểm: 100 / 100</div>
      <div class="f-date">{{{{ frappe.utils.formatdate(doc.issue_date) or '09-04-2026' }}}}</div>
      <div class="f-sig">Lê Minh Trí</div>
      <img class="f-seal" src="{seal_data_uri}" alt="Seal"/>
    </div>
  </div>
</div>
</body>
</html>"""

    if frappe.db.exists("Print Format", fmt_name):
        doc = frappe.get_doc("Print Format", fmt_name)
        doc.html = hack_html
        doc.save(ignore_permissions=True)
    
    frappe.db.commit()
    print(f"SYNC COMPLETE: {fmt_name} (16:9 Centered + Base64 Seal)")

if __name__ == "__main__":
    run()
