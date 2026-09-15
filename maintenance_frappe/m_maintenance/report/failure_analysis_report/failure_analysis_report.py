import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Failure Category", "fieldname": "failure_category", "fieldtype": "Data", "width": 150},
        {"label": "Failure Type", "fieldname": "failure_type", "fieldtype": "Data", "width": 150},
        {"label": "Failure Mode", "fieldname": "failure_mode", "fieldtype": "Data", "width": 150}
    ]
    data = frappe.get_all("Maintenance Root Cause Analysis", fields=["equipment", "failure_category", "failure_type", "failure_mode"])
    return columns, data
