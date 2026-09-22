import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Work Order ID", "fieldname": "name", "fieldtype": "Link", "options": "Work Order", "width": 140},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 140},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 120},
        {"label": "Priority", "fieldname": "priority", "fieldtype": "Data", "width": 100},
        {"label": "Type", "fieldname": "maintenance_type", "fieldtype": "Data", "width": 120},
        {"label": "Technician", "fieldname": "assigned_technician", "fieldtype": "Link", "options": "Employee", "width": 140},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 120}
    ]
    data = frappe.get_all("Work Order", fields=["name", "equipment", "status", "priority", "maintenance_type", "assigned_technician", "total_cost"], order_by="creation desc")
    return columns, data
