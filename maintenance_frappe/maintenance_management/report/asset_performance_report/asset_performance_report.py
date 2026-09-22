import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Equipment", "fieldname": "equipment_id", "fieldtype": "Link", "options": "Equipment", "width": 140},
        {"label": "Equipment Name", "fieldname": "equipment_name", "fieldtype": "Data", "width": 180},
        {"label": "Condition", "fieldname": "criticality", "fieldtype": "Data", "width": 120},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120}
    ]
    data = frappe.get_all("Equipment", fields=["equipment_id", "equipment_name", "criticality", "status"])
    return columns, data
