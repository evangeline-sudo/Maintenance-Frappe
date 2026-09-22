import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Team", "fieldname": "assigned_team", "fieldtype": "Link", "options": "Maintenance Team", "width": 160},
        {"label": "Total Orders", "fieldname": "total_orders", "fieldtype": "Int", "width": 130},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 140}
    ]
    data = frappe.db.sql("SELECT assigned_team, COUNT(name) as total_orders, SUM(total_cost) as total_cost FROM `tabWork Order` GROUP BY assigned_team", as_dict=True)
    return columns, data
