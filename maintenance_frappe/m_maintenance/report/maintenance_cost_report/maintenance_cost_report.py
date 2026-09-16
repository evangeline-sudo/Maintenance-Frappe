import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Labor Cost", "fieldname": "labor_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Parts Cost", "fieldname": "parts_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Tool Cost", "fieldname": "tool_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Vendor Cost", "fieldname": "vendor_cost", "fieldtype": "Currency", "width": 120},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 140}
    ]
    data = frappe.get_all("Work Order", fields=["equipment", "labor_cost", "parts_cost", "tool_cost", "vendor_cost", "total_cost"])
    return columns, data
