import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
import random

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()
    frappe.flags.in_test = True

    print("--- Bắt đầu tạo dữ liệu 10 khóa học & Hackathon ---")

    student_email = "coder@example.com"
    evaluator_email = "tuantm@domain.com"
    
    # 1. Tạo Học Viên
    if not frappe.db.exists("User", student_email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": student_email,
            "first_name": "Siêu",
            "last_name": "Lập Trình",
            "send_welcome_email": 0,
            "roles": [{"role": "LMS Student"}]
        })
        user.insert(ignore_permissions=True)
        print(f"-> Tạo học viên: {student_email}")

    # Đảm bảo evaluator tồn tại
    if not frappe.db.exists("Course Evaluator", evaluator_email):
        if getattr(frappe.db, "exists", None)("User", evaluator_email):
            ce = frappe.get_doc({
                "doctype": "Course Evaluator",
                "evaluator": evaluator_email,
                "evaluator_name": "Lê Minh Tuấn"
            })
            ce.insert(ignore_permissions=True)

    # Các khóa học lập trình
    courses = [
        {"id": "python-basic", "title": "Python Cơ Bản", "color1": "#306998", "color2": "#FFE873"},
        {"id": "js-advanced", "title": "JavaScript Chuyên Sâu", "color1": "#F0DB4F", "color2": "#323330"},
        {"id": "react-mastery", "title": "ReactJS Masterclass", "color1": "#61DBFB", "color2": "#282C34"},
        {"id": "java-spring", "title": "Java Spring Boot", "color1": "#5382A1", "color2": "#F8981D"},
        {"id": "csharp-dotnet", "title": "C# .NET Core", "color1": "#9B4F96", "color2": "#ffffff"},
        {"id": "go-lang", "title": "Golang System Programming", "color1": "#00ADD8", "color2": "#E0EBF5"},
        {"id": "rust-safe", "title": "Rust Safe Concurrency", "color1": "#DEA584", "color2": "#000000"},
        {"id": "sql-db", "title": "SQL & Database Design", "color1": "#F29111", "color2": "#00758F"},
        {"id": "docker-k8s", "title": "DevOps: Docker & K8s", "color1": "#2496ED", "color2": "#326CE5"},
        {"id": "aws-cloud", "title": "AWS Cloud Architect", "color1": "#FF9900", "color2": "#232F3E"}
    ]

    logo_svg = """<svg viewBox="0 0 24 24" style="width:26px; height:26px; fill:#fff;"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>"""

    # Function tạo HTML Print Format cho từng khóa
    def get_html_template(course_title, c1, c2):
        return f"""
<!DOCTYPE html>
<html lang="vi">
<head>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    @page {{ size: A4 landscape; margin: 0; }}
    html, body {{ width: 297mm; height: 210mm; background: #fff; font-family: 'Helvetica', sans-serif; overflow:hidden; }}
    .cert-wrapper {{ position: relative; width: 100%; height: 100%; background: linear-gradient(135deg, {c2} 0%, #fff 50%, {c2} 100%); }}
    .border-1 {{ position: absolute; top: 10mm; left: 10mm; right: 10mm; bottom: 10mm; border: 3px solid {c1}; }}
    .border-2 {{ position: absolute; top: 12mm; left: 12mm; right: 12mm; bottom: 12mm; border: 1px solid {c1}; opacity: 0.5; }}
    .content {{ position: relative; z-index: 10; text-align: center; padding-top: 30mm; }}
    .logo {{ width: 50px; height: 50px; background: {c1}; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 2mm; }}
    .title {{ font-size: 40px; color: {c1}; font-weight: bold; margin-bottom: 5mm; text-transform: uppercase; }}
    .subtitle {{ font-size: 16px; color: #555; }}
    .name {{ font-size: 35px; color: #333; margin: 5mm 0; font-weight: bold; }}
    .course {{ font-size: 22px; color: {c1}; font-weight: 600; margin-bottom: 10mm; }}
    .footer {{ display: flex; justify-content: space-around; margin-top: 15mm; align-items: flex-end; }}
    .sig {{ border-top: 1px solid #333; width: 150px; padding-top: 5px; font-size: 12px; }}
    .seal {{ width: 80px; height: 80px; border-radius: 50%; border: 3px dashed {c1}; display: flex; align-items: center; justify-content: center; font-size:10px; font-weight:bold; color:{c1}; }}
  </style>
</head>
<body>
  <div class="cert-wrapper">
    <!-- Hình ảnh trang trí (viền) dùng thẻ img -->
    <img src="/files/phoi.jpg" style="display:none;"/> <!-- Placeholder logic -->
    <div class="border-1"></div><div class="border-2"></div>
    <div class="content">
      <div class="logo">{logo_svg}</div>
      <div class="title">Chứng Chỉ Hoàn Thành</div>
      <div class="subtitle">Được cấp cho học viên xuất sắc</div>
      <div class="name">{{{{ doc.member_name or doc.full_name }}}}</div>
      <div class="subtitle">Vì đã hoàn thành khóa học lập trình</div>
      <div class="course">{{{{ doc.course_title or doc.course }}}}</div>
      <div class="footer">
        <div>
          <div style="font-size: 20px; font-family: cursive; margin-bottom:2px;">{{{{ doc.evaluator_name }}}}</div>
          <div class="sig">Giảng viên / Instructor</div>
        </div>
        <div class="seal">SEAL<br/>OFFICIAL</div>
        <div>
          <div style="margin-bottom:5px;">{{{{ frappe.utils.formatdate(doc.issue_date) }}}}</div>
          <div class="sig">Ngày cấp / Date</div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>"""

    # Tạo 10 khóa học và print formats
    for c in courses:
        fmt_name = f"Cert_Fmt_{c['id']}"
        if not frappe.db.exists("Print Format", fmt_name):
            fmt = frappe.get_doc({
                "doctype": "Print Format", "name": fmt_name,
                "doc_type": "LMS Certificate", "module": "LMS",
                "custom_format": 1, "html": get_html_template(c['title'], c['color1'], c['color2'])
            })
            fmt.insert(ignore_permissions=True)

        course_name = frappe.db.get_value("LMS Course", {"title": c['title']}, "name")
        if not course_name:
            course = frappe.get_doc({
                "doctype": "LMS Course", "title": c['title'], "published": 1, "enable_certification": 1,
                "short_introduction": f"Khóa học {c['title']}", "description": f"Học {c['title']} từ A-Z.",
                "instructors": [{"instructor": evaluator_email}]
            })
            course.insert(ignore_permissions=True)
            course_name = course.name

        # Enroll & Issue
        if not frappe.db.exists("LMS Enrollment", {"course": course_name, "member": student_email}):
            frappe.get_doc({"doctype": "LMS Enrollment", "course": course_name, "member": student_email, "progress": 100}).insert(ignore_permissions=True)
        else:
            enr_name = frappe.db.get_value("LMS Enrollment", {"course": course_name, "member": student_email}, "name")
            frappe.db.set_value("LMS Enrollment", enr_name, "progress", 100)

        if not frappe.db.exists("LMS Certificate", {"course": course_name, "member": student_email}):
            cert = frappe.get_doc({"doctype": "LMS Certificate", "course": course_name, "member": student_email, "evaluator": evaluator_email, "template": fmt_name, "issue_date": nowdate()})
            cert.insert(ignore_permissions=True)
            print(f"-> Đã cấp chứng chỉ cho {c['title']}")

    # ==========================
    # KHÓA HỌC HACKATHON ĐẶC BIỆT
    # ==========================
    hackathon_fmt_name = "Cert_Fmt_Hackathon"
    # Dùng <img> làm background, logo...
    hack_html = """<!DOCTYPE html>
<html lang="vi">
<head>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    @page { size: A4 landscape; margin: 0; }
    html, body { width: 297mm; height: 210mm; position: relative; overflow: hidden; font-family: 'Helvetica', sans-serif;}
    
    /* Chèn ảnh nền bằng thẻ img absolute */
    .bg-img {
       position: absolute; top:0; left:0; width:100%; height:100%; z-index: -2;
       object-fit: cover;
    }
    /* Chèn viền trang trí bằng thẻ img */
    .decor-frame {
       position: absolute; top: 10mm; left: 10mm; right: 10mm; bottom: 10mm; z-index: -1;
       border: 5px double #FFD700; /* fall back */
    }

    .content-h { position: relative; z-index: 10; text-align: center; padding-top: 35mm; color: #fff;}
    .logo-img { width: 80px; margin-bottom: 3mm; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }
    .title-h { font-size: 55px; font-weight: 800; color: #FFD700; text-shadow: 2px 2px 4px #000; text-transform: uppercase; margin-bottom: 2mm;}
    .sub-h { font-size: 20px; font-weight: bold; text-shadow: 1px 1px 2px #000; }
    .name-h { font-size: 45px; font-weight: 900; color: #FFF; text-shadow: 0 0 10px #FFD700; margin: 8mm 0;}
    .seal-img { position: absolute; bottom: 20mm; right: 25mm; width: 100px; height: 100px; }
    .sig-area { position: absolute; bottom: 20mm; left: 25mm; text-align: center; width: 200px; }
  </style>
</head>
<body>
  <!-- TRUYỀN ẢNH BACKGROUND TỪ FILE (phoi.jpg) -->
  <img class="bg-img" src="/files/phoi.jpg" alt="Background"/>

  <div class="decor-frame"></div>

  <div class="content-h">
    <!-- LOGO CHÈN BẰNG IMG -->
    <img class="logo-img" src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/GitHub_Invertocat_Logo.svg/1024px-GitHub_Invertocat_Logo.svg.png" alt="Logo"/>
    
    <div class="title-h">Hackathon Champion</div>
    <div class="sub-h">Global Coding Hackathon 2026</div>
    <div class="name-h">{{ doc.member_name or doc.full_name }}</div>
    <div class="sub-h">Course: {{ doc.course_title or doc.course }}<br/>Score: {{ doc.score or "98.5" }} / 100</div>
  </div>

  <div class="sig-area">
    <div style="font-size:24px; font-family:cursive; color:#FFD700;">{{ doc.evaluator_name }}</div>
    <div style="border-top: 2px solid #FFF; margin-top:2px; font-weight:bold; color:#FFF; padding-top:2px;">Trưởng Ban Tổ Chức</div>
  </div>

  <!-- CON DẤU BẰNG IMG -->
  <img class="seal-img" src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Seal_of_Approval.svg/1200px-Seal_of_Approval.svg.png" alt="Seal"/>
</body>
</html>"""

    if not frappe.db.exists("Print Format", hackathon_fmt_name):
        frappe.get_doc({"doctype": "Print Format", "name": hackathon_fmt_name, "doc_type": "LMS Certificate", "module": "LMS", "custom_format": 1, "html": hack_html}).insert(ignore_permissions=True)
    else:
        fmt = frappe.get_doc("Print Format", hackathon_fmt_name)
        fmt.html = hack_html
        fmt.save(ignore_permissions=True)

    hack_course_name = frappe.db.get_value("LMS Course", {"title": "Siêu Hackathon 2026"}, "name")
    if not hack_course_name:
        hack_course = frappe.get_doc({"doctype": "LMS Course", "title": "Siêu Hackathon 2026", "published": 1, "enable_certification": 1, "short_introduction": "Hackathon khủng", "description": "Lập trình thâu đêm.", "instructors": [{"instructor": evaluator_email}]})
        hack_course.insert(ignore_permissions=True)
        hack_course_name = hack_course.name

    if not frappe.db.exists("LMS Enrollment", {"course": hack_course_name, "member": student_email}):
        frappe.get_doc({"doctype": "LMS Enrollment", "course": hack_course_name, "member": student_email, "progress": 100}).insert(ignore_permissions=True)
    else:
        enr_name = frappe.db.get_value("LMS Enrollment", {"course": hack_course_name, "member": student_email}, "name")
        frappe.db.set_value("LMS Enrollment", enr_name, "progress", 100)

    if not frappe.db.exists("LMS Certificate", {"course": hack_course_name, "member": student_email}):
        cert = frappe.get_doc({"doctype": "LMS Certificate", "course": hack_course_name, "member": student_email, "evaluator": evaluator_email, "template": hackathon_fmt_name, "issue_date": nowdate()})
        cert.insert(ignore_permissions=True)
        print("-> Đã cấp chứng chỉ HACKATHON")

    frappe.db.commit()
    print("--- HOÀN TẤT ---")

if __name__ == "__main__":
    run()
