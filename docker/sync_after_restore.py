import frappe
import os

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()

    # 1. LMS Certificate Premium
    pf_premium = "LMS Certificate Premium"
    html_premium_path = "/workspace/tmp_templates/lms_certificate_print_format.html"
    
    with open(html_premium_path, "r", encoding="utf-8") as f:
        html_premium = f.read()

    if not frappe.db.exists("Print Format", pf_premium):
        doc = frappe.get_doc({
            "doctype": "Print Format",
            "name": pf_premium,
            "doc_type": "LMS Certificate",
            "module": "LMS",
            "custom_format": 1,
            "html": html_premium
        })
        doc.insert(ignore_permissions=True)
        print(f"✅ Created {pf_premium}")
    else:
        doc = frappe.get_doc("Print Format", pf_premium)
        doc.html = html_premium
        doc.save(ignore_permissions=True)
        print(f"✅ Updated {pf_premium}")

    # 2. Chứng Nhận WEB AI HACKATHON 2026
    # Dùng nội dung đã có trong DB nhưng thêm seal vào
    pf_hackathon_name = "Chứng Nhận WEB AI HACKATHON 2026"
    if frappe.db.exists("Print Format", pf_hackathon_name):
        doc = frappe.get_doc("Print Format", pf_hackathon_name)
        
        # Thêm CSS seal
        seal_css = """
    .f-seal {
        position: absolute;
        right: 50px;
        bottom: 50px;
        width: 100px;
        height: 100px;
        opacity: 0.95;
        transform: rotate(-8deg);
        mix-blend-mode: multiply;
        filter: drop-shadow(0 1px 3px rgba(0,0,0,0.1));
        z-index: 10;
        pointer-events: none;
    }
"""
        if ".f-seal" not in doc.html:
            doc.html = doc.html.replace("</style>", seal_css + "\n</style>")
        
        # Thêm thẻ img seal
        seal_img = '<img class="f-seal" src="/assets/lms/images/MOCCHUNGCHI.png" alt="Seal"/>'
        if "MOCCHUNGCHI.png" not in doc.html:
            doc.html = doc.html.replace('</div>\n</div>', seal_img + '\n    </div>\n</div>')
        
        doc.save(ignore_permissions=True)
        print(f"✅ Updated {pf_hackathon_name} with seal")
    else:
        print(f"❌ {pf_hackathon_name} not found in DB")

    frappe.db.commit()
    frappe.destroy()

if __name__ == "__main__":
    run()
