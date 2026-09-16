import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Technician", "fieldname": "assigned_technician", "fieldtype": "Link", "options": "Responsible Person", "width": 160},
        {"label": "Completed Orders", "fieldname": "completed_orders", "fieldtype": "Int", "width": 130},
        {"label": "Total Labor Cost", "fieldname": "total_labor", "fieldtype": "Currency", "width": 140}
    ]
    data = frappe.db.sql("SELECT assigned_technician, COUNT(name) as completed_orders, SUM(labor_cost) as total_labor FROM `tabWork Order` WHERE status IN ('Resolved', 'Completed') GROUP BY assigned_technician", as_dict=True)
    return columns, data
