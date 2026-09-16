import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Failure Count", "fieldname": "failure_count", "fieldtype": "Int", "width": 140}
    ]
    data = frappe.db.sql("SELECT equipment, COUNT(name) as failure_count FROM `tabMaintenance Request` WHERE equipment IS NOT NULL GROUP BY equipment HAVING failure_count >= 1", as_dict=True)
    return columns, data
