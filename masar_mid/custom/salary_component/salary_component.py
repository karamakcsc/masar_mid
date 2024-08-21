import frappe
from frappe import _

@frappe.whitelist()
def update_formula_via_api(docname, formula_value):
    if not frappe.has_permission("Salary Component", "write", docname):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    frappe.db.set_value("Salary Component", docname, "formula", formula_value, update_modified=False)
    frappe.db.commit()