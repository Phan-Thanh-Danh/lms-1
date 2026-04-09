import frappe
from frappe.utils import nowdate
import base64
import os

def run():
    # 1. SETUP PRINT FORMAT
    fmt_name = "Cert_Fmt_Hackathon"
    phoi_path = "/workspace/phoi.jpg"
    
    with open(phoi_path, "rb") as f:
        phoi_b64 = base64.b64encode(f.read()).decode('utf-8')
    phoi_data_uri = f"data:image/jpeg;base64,{phoi_b64}"

    hack_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  @page {{ size: A4 landscape; margin: 0; }}
  html, body {{ width: 100%; height: 100%; font-family: Arial, sans-serif; }}
  .page {{ position: relative; width: 297mm; height: 210mm; }}
  .page img.bg {{ position: absolute; top: 0; left: 0; width: 297mm; height: 210mm; object-fit: fill; }}
  .overlay {{ position: absolute; top: 0; left: 0; width: 297mm; height: 210mm; }}
  .f-name {{ position: absolute; left: 0; width: 297mm; top: 85mm; text-align: center; font-size: 45px; font-weight: 900; color: #1a1a1a; text-transform: uppercase; }}
  .f-course {{ position: absolute; left: 0; width: 297mm; top: 115mm; text-align: center; font-size: 28px; font-weight: bold; color: #333; }}
  .f-score {{ position: absolute; left: 0; width: 297mm; top: 135mm; text-align: center; font-size: 20px; color: #555; }}
  .f-date {{ position: absolute; left: 65mm; top: 165mm; text-align: center; width: 60mm; font-size: 18px; color: #111; }}
  .f-sig {{ position: absolute; right: 65mm; top: 165mm; text-align: center; width: 60mm; font-size: 20px; font-weight: bold; font-style: italic; color: #111; }}
  .f-seal {{
    position: absolute;
    right: 48mm;
    top: 172mm;
    width: 23mm;
    height: 23mm;
    opacity: 0.95;
    transform: rotate(-8deg);
    mix-blend-mode: multiply;
    z-index: 10;
  }}
</style>
</head>
<body>
<div class="page">
  <img class="bg" src="{phoi_data_uri}" alt=""/>
  <div class="overlay">
    <div class="f-name">{{{{ doc.member_name or 'Học Viên' }}}}</div>
    <div class="f-course">{{{{ doc.course or 'Hackathon' }}}}</div>
    <div class="f-score">Điểm: 100 / 100</div>
    <div class="f-date">{{{{ frappe.utils.formatdate(doc.issue_date) }}}}</div>
    <div class="f-sig">Lê Minh Trí</div>
    <img class="f-seal" src="/assets/lms/images/MOCCHUNGCHI.png" alt="Seal"/>
  </div>
</div>
</body>
</html>"""

    if not frappe.db.exists("Print Format", fmt_name):
        doc = frappe.get_doc({
            "doctype": "Print Format",
            "name": fmt_name,
            "doc_type": "LMS Certificate",
            "module": "LMS",
            "custom_format": 1,
            "html": hack_html,
            "orientation": "Landscape"
        })
        doc.insert(ignore_permissions=True)
    else:
        doc = frappe.get_doc("Print Format", fmt_name)
        doc.html = hack_html
        doc.orientation = "Landscape"
        doc.save(ignore_permissions=True)

    # 2. CREATE COURSE
    course_id = "web-ai-hackathon-2026"
    if not frappe.db.exists("LMS Course", course_id):
        course = frappe.get_doc({
            "doctype": "LMS Course",
            "title": "Web AI Hackathon 2026",
            "name": course_id,
            "published": 1,
            "enable_certification": 1,
            "short_introduction": "Khóa học Hackathon 2026",
            "description": "Mô tả khóa học Web AI Hackathon 2026",
            "instructors": [
                {"instructor": "Administrator"}
            ]
        })
        course.insert(ignore_permissions=True)
    
    # 3. ENROLL & PASS
    student = "Administrator"
    enrol_name = frappe.db.get_value("LMS Enrollment", {"course": course_id, "member": student})
    if not enrol_name:
        enrol = frappe.get_doc({
            "doctype": "LMS Enrollment",
            "course": course_id,
            "member": student,
            "progress": 100
        })
        enrol.insert(ignore_permissions=True)
    else:
        frappe.db.set_value("LMS Enrollment", enrol_name, "progress", 100)

    # 4. ISSUE CERTIFICATE
    cert_name = frappe.db.get_value("LMS Certificate", {"member": student, "course": course_id})
    if not cert_name:
        cert = frappe.get_doc({
            "doctype": "LMS Certificate",
            "member": student,
            "course": course_id,
            "template": fmt_name,
            "issue_date": nowdate(),
            "evaluator_name": "Lê Minh Trí"
        })
        cert.insert(ignore_permissions=True)
        cert_name = cert.name
    
    frappe.db.commit()
    print(f"COMPLETE: {cert_name}")

if __name__ == "__main__":
    run()
