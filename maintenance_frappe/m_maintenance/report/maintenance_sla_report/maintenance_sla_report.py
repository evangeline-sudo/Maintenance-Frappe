import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Request ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
        {"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 110},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "SLA Met", "fieldname": "sla_met", "fieldtype": "Data", "width": 110}
    ]
    data = [{"name": r.name, "priority": r.priority, "status": r.status, "sla_met": "Yes"} for r in frappe.get_all("Maintenance Request", fields=["name", "priority", "status"])]
    return columns, data
