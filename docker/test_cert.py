import frappe
from frappe.utils import nowdate
from frappe.model.document import Document

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()

    # Create dummy print format to avoid validation errors if required
    # But wait, earlier we already created an HTML print format. We can just inject it programmatically!
    with open('/workspace/tmp_templates/lms_certificate_print_format.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    default_template = "LMS Certificate Premium"
    if not frappe.db.exists("Print Format", default_template):
        template = frappe.get_doc({
            "doctype": "Print Format",
            "name": default_template,
            "doc_type": "LMS Certificate",
            "module": "LMS",
            "custom_format": 1,
            "html": html_content
        })
        template.insert(ignore_permissions=True)
        print(f"Created Template: {default_template}")
    
    frappe.db.set_value('LMS Settings', None, 'default_certificate_template', default_template)

    # 1. Create a Student
    if not frappe.db.exists("User", "test_student@example.com"):
        user = frappe.get_doc({
            "doctype": "User",
            "email": "test_student@example.com",
            "first_name": "Test",
            "last_name": "Student",
            "send_welcome_email": 0,
            "roles": [{"role": "LMS Student"}]
        })
        user.insert(ignore_permissions=True)
        print("Created test student")

    # 2. Create an Evaluator
    if not frappe.db.exists("User", "test_evaluator@example.com"):
        evaluator = frappe.get_doc({
            "doctype": "User",
            "email": "test_evaluator@example.com",
            "first_name": "Test",
            "last_name": "Evaluator",
            "send_welcome_email": 0,
            "roles": [{"role": "Batch Evaluator"}]
        })
        evaluator.insert(ignore_permissions=True)
        print("Created test evaluator")

    if not frappe.db.exists("Course Evaluator", "test_evaluator@example.com"):
        course_evaluator = frappe.get_doc({
            "doctype": "Course Evaluator",
            "evaluator": "test_evaluator@example.com",
            "evaluator_name": "Test Evaluator"
        })
        course_evaluator.insert(ignore_permissions=True)
        print("Created Course Evaluator record")

    # 3. Create a Course
    course_name = "test-course-certificates"
    if not frappe.db.exists("LMS Course", course_name):
        course = frappe.get_doc({
            "doctype": "LMS Course",
            "title": "Test Course Certificates",
            "name": course_name,
            "published": 1,
            "enable_certification": 1,
            "instructors": [{"instructor": "test_evaluator@example.com"}],
            "short_introduction": "Test Course Short Intro",
            "description": "Test Course Description that is a bit longer than the short intro."
        })
        course.insert(ignore_permissions=True)
        print("Created test course")
    else:
        # ensure certification is enabled
        course = frappe.get_doc("LMS Course", course_name)
        if getattr(course, "enable_certification", None) != 1:
             course.enable_certification = 1
             course.save(ignore_permissions=True)
             print("Enabled certification for course")


    # 4. Enroll the student
    if not frappe.db.exists("LMS Enrollment", {"course": course_name, "member": "test_student@example.com"}):
        enrollment = frappe.get_doc({
            "doctype": "LMS Enrollment",
            "course": course_name,
            "member": "test_student@example.com",
            "progress": 100 # Mark as complete!
        })
        enrollment.insert(ignore_permissions=True)
        print("Enrolled student and marked progress as 100%")
    else:
        # Ensure progress is 100%
        enrollment_name = frappe.db.get_value("LMS Enrollment", {"course": course_name, "member": "test_student@example.com"})
        enrollment = frappe.get_doc("LMS Enrollment", enrollment_name)
        if enrollment.progress != 100:
            enrollment.progress = 100
            enrollment.save(ignore_permissions=True)
            print("Updated enrollment progress to 100%")

    # 5. Issue Certificate
    certificate_name = frappe.db.exists("LMS Certificate", {"member": "test_student@example.com", "course": course_name})
    if not certificate_name:
        from lms.lms.doctype.lms_certificate.lms_certificate import create_certificate
        frappe.session.user = "test_student@example.com"
        try:
            cert = create_certificate(course_name)
            frappe.db.commit()
            print(f"SUCCESS: Certificate created with name: {cert.name}")
        except Exception as e:
             print(f"FAILED to create certificate: {e}")
             frappe.db.rollback()
             
             # Fallback manual creation
             frappe.session.user = "Administrator" # Restoring admin session for manual creation
             print("Attempting manual creation...")
             cert = frappe.get_doc({
                 "doctype": "LMS Certificate",
                 "member": "test_student@example.com",
                 "course": course_name,
                 "evaluator": "test_evaluator@example.com",
                 "template": default_template,
                 "issue_date": nowdate()
             })
             cert.insert(ignore_permissions=True)
             frappe.db.commit()
             print(f"SUCCESS: Certificate generated via manual fallback: {cert.name}")

    else:
        cert = frappe.get_doc("LMS Certificate", certificate_name)
        print(f"Certificate already exists: {certificate_name}")
        print(f"Details - ID: {cert.name}, Member: {cert.member_name}, Course: {cert.course_title}, Template: {cert.template}")

    frappe.destroy()

if __name__ == "__main__":
    run()
