import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Plan Name", "fieldname": "name", "fieldtype": "Link", "options": "Preventive Maintenance Plan", "width": 160},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 140},
        {"label": "Frequency", "fieldname": "frequency", "fieldtype": "Data", "width": 120},
        {"label": "Next Due Date", "fieldname": "next_due_date", "fieldtype": "Date", "width": 130},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110}
    ]
    data = frappe.get_all("Preventive Maintenance Plan", fields=["name", "equipment", "frequency", "next_due_date", "status"], order_by="next_due_date asc")
    return columns, data
