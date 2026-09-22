import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Part ID", "fieldname": "part_id", "fieldtype": "Link", "options": "Maintenance Spare Part", "width": 140},
        {"label": "Part Name", "fieldname": "part_name", "fieldtype": "Data", "width": 180},
        {"label": "Available Qty", "fieldname": "quantity_available", "fieldtype": "Float", "width": 130},
        {"label": "Minimum Stock", "fieldname": "minimum_stock", "fieldtype": "Float", "width": 130},
        {"label": "Reorder Level", "fieldname": "reorder_level", "fieldtype": "Float", "width": 130}
    ]
    data = frappe.get_all("Maintenance Spare Part", fields=["part_id", "part_name", "quantity_available", "minimum_stock", "reorder_level"])
    return columns, data
