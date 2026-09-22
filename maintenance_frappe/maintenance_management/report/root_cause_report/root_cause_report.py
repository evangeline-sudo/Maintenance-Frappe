import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "RCA ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Root Cause Analysis", "width": 140},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Root Cause", "fieldname": "root_cause", "fieldtype": "Data", "width": 200},
        {"label": "Corrective Action", "fieldname": "corrective_action", "fieldtype": "Data", "width": 200}
    ]
    data = frappe.get_all("Maintenance Root Cause Analysis", fields=["name", "equipment", "root_cause", "corrective_action"])
    return columns, data
