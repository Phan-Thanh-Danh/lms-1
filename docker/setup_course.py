import frappe
from frappe.model.document import Document

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()
    
    frappe.flags.in_test = True # prevent some validations if any

    print("--- Bắt đầu cài đặt Data ---")

    # 1. Cài đặt Print Format từ file đã tạo
    print("1. Đang cài đặt Template Chứng chỉ...")
    with open('/workspace/tmp_templates/lms_certificate_print_format.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    template_name = "LMS Certificate Premium"
    if not frappe.db.exists("Print Format", template_name):
        template = frappe.get_doc({
            "doctype": "Print Format",
            "name": template_name,
            "doc_type": "LMS Certificate",
            "module": "LMS",
            "custom_format": 1,
            "html": html_content
        })
        template.insert(ignore_permissions=True)
        print(f"   -> Đã tạo Print Format '{template_name}'")
    else:
        # Cập nhật template nếu đã tồn tại
        template = frappe.get_doc("Print Format", template_name)
        template.html = html_content
        template.save(ignore_permissions=True)
        print(f"   -> Đã cập nhật Print Format '{template_name}'")

    # Đặt template này làm mặc định trong LMS Settings
    frappe.db.set_value('LMS Settings', None, 'default_certificate_template', template_name)
    print("   -> Đã set làm template mặc định!")

    # 2. Tạo Giảng viên (Course Evaluator) - Cần thiết cho chứng chỉ
    evaluator_email = "tuantm@domain.com"
    if not frappe.db.exists("User", evaluator_email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": evaluator_email,
            "first_name": "Lê Minh",
            "last_name": "Tuấn",
            "send_welcome_email": 0,
            "roles": [{"role": "Batch Evaluator"}]
        })
        user.insert(ignore_permissions=True)
        
    if not frappe.db.exists("Course Evaluator", evaluator_email):
        course_evaluator = frappe.get_doc({
            "doctype": "Course Evaluator",
            "evaluator": evaluator_email,
            "evaluator_name": "Lê Minh Tuấn"
        })
        course_evaluator.insert(ignore_permissions=True)

    # 3. Tạo Khóa học Marketing Digital
    print("2. Đang tạo khóa học 'Marketing Digital'...")
    course_title = "Tiếp Thị Kỹ Thuật Số (Marketing Digital) Chuyên Sâu"
    course_name = frappe.db.get_value("LMS Course", {"title": course_title}, "name")
    
    if not course_name:
        course = frappe.get_doc({
            "doctype": "LMS Course",
            "title": course_title,
            "published": 1,
            "enable_certification": 1, # BẬT CHỨNG CHỈ
            "short_introduction": "Trở thành chuyên gia Digital Marketing sau 30 ngày.",
            "description": "Khóa học cung cấp kiến thức toàn diện về SEO, Quảng cáo Facebook, Google Ads, và Content Marketing.",
            "instructors": [{"instructor": evaluator_email}]
        })
        course.insert(ignore_permissions=True)
        course_name = course.name
        print(f"   -> Đã tạo khóa học '{course_title}'")
    else:
        # Update settings just in case
        course = frappe.get_doc("LMS Course", course_name)
        if getattr(course, "enable_certification", 0) == 0:
            course.enable_certification = 1
            course.save(ignore_permissions=True)
            print("   -> Đã bật cấp chứng chỉ cho khóa học")

    # 4. Tạo các chương (Chương 1)
    chapter_title = "Chương 1: Tổng quan về Digital Marketing"
    chapter_name = frappe.db.get_value("Course Chapter", {"title": chapter_title, "course": course.name}, "name")
    if not chapter_name:
        chapter = frappe.get_doc({
            "doctype": "Course Chapter",
            "title": chapter_title,
            "course": course.name
        })
        chapter.insert(ignore_permissions=True)
        chapter_name = chapter.name
        print("   -> Đã tạo Chương 1")
    else:
        print("   -> Đã tồn tại Chương 1")
    
    # Tạo bài học
    lesson_title = "Bài 1: Nhập môn Marketing"
    lesson_name = frappe.db.get_value("Course Lesson", {"title": lesson_title, "chapter": chapter_name}, "name")
    if not lesson_name:
        lesson = frappe.get_doc({
            "doctype": "Course Lesson",
            "title": lesson_title,
            "chapter": chapter_name,
            "body": "Nội dung bài học giới thiệu về tiếp thị kỹ thuật số."
        })
        lesson.insert(ignore_permissions=True)
        print("   -> Đã tạo Bài 1")
    else:
        print("   -> Đã tồn tại Bài 1")

    # 5. Ghi danh cho Administrator (để Admin có sẵn chứng chỉ test)
    admin_email = "Administrator"
    print(f"3. Cấp sẵn chứng chỉ cho user {admin_email} để bạn xem demo...")
    
    # 5.1 Ghi danh
    if not frappe.db.exists("LMS Enrollment", {"course": course_name, "member": admin_email}):
        enrollment = frappe.get_doc({
            "doctype": "LMS Enrollment",
            "course": course_name,
            "member": admin_email,
            "progress": 100 # Mô phỏng học xong 100%
        })
        enrollment.insert(ignore_permissions=True)
    else:
        enrollment_id = frappe.db.get_value("LMS Enrollment", {"course": course_name, "member": admin_email}, "name")
        enrollment = frappe.get_doc("LMS Enrollment", enrollment_id)
        if enrollment.progress != 100:
            enrollment.db_set("progress", 100)

    # 5.2 Tạo chứng chỉ
    from frappe.utils import nowdate
    certificate_id = frappe.db.exists("LMS Certificate", {"member": admin_email, "course": course_name})
    if not certificate_id:
        cert = frappe.get_doc({
            "doctype": "LMS Certificate",
            "member": admin_email,
            "course": course_name,
            "evaluator": evaluator_email,
            "template": template_name,
            "issue_date": nowdate()
        })
        cert.insert(ignore_permissions=True)
        print(f"   -> ĐÃ CẤP CHỨNG CHỈ (ID: {cert.name})")
    else:
        print(f"   -> Admin {admin_email} đã có chứng chỉ (ID: {certificate_id})")

    frappe.db.commit()
    print("--- HOÀN TẤT SETUP ---")
    frappe.destroy()

if __name__ == "__main__":
    run()
