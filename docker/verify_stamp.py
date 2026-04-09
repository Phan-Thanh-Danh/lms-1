import frappe

def run():
    frappe.init(site="lms.localhost")
    frappe.connect()
    
    name = frappe.db.get_value("LMS Certificate", {}, "name")
    if not name:
        print("❌ No certificate found in DB")
        return

    print(f"Testing for certificate: {name}")
    html = frappe.get_print("LMS Certificate", name, "LMS Certificate Premium")
    
    checks = {
        "MOCCHUNGCHI.png": "/files/MOCCHUNGCHI.png" in html,
        "cert-stamp-img": "cert-stamp-img" in html,
        "transform: rotate(-8deg)": "rotate(-8deg)" in html,
        "drop-shadow": "drop-shadow" in html
    }
    
    for key, val in checks.items():
        if val:
            print(f"✅ {key} found")
        else:
            print(f"❌ {key} NOT found")

if __name__ == "__main__":
    run()
