import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Warranty ID", "fieldname": "name", "fieldtype": "Link", "options": "Asset Warranty", "width": 140},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Provider", "fieldname": "warranty_provider", "fieldtype": "Data", "width": 150},
        {"label": "End Date", "fieldname": "end_date", "fieldtype": "Date", "width": 130},
        {"label": "Status", "fieldname": "warranty_status", "fieldtype": "Data", "width": 120}
    ]
    data = frappe.get_all("Asset Warranty", fields=["name", "equipment", "warranty_provider", "end_date", "warranty_status"])
    return columns, data
