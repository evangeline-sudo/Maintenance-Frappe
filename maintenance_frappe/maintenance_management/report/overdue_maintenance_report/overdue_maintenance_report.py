import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Work Order", "fieldname": "name", "fieldtype": "Link", "options": "Work Order", "width": 140},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 140},
        {"label": "Planned Start", "fieldname": "planned_start", "fieldtype": "Datetime", "width": 140},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120}
    ]
    data = frappe.get_all("Work Order", filters={"status": ["in", ["Draft", "Scheduled", "In Progress"]]}, fields=["name", "equipment", "planned_start", "status"])
    return columns, data
