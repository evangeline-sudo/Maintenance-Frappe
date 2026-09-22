import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Downtime ID", "fieldname": "name", "fieldtype": "Link", "options": "Asset Downtime", "width": 140},
        {"label": "Equipment", "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 150},
        {"label": "Start", "fieldname": "downtime_start", "fieldtype": "Datetime", "width": 140},
        {"label": "End", "fieldname": "downtime_end", "fieldtype": "Datetime", "width": 140},
        {"label": "Downtime Hours", "fieldname": "total_downtime_hours", "fieldtype": "Float", "width": 140}
    ]
    data = frappe.get_all("Asset Downtime", fields=["name", "equipment", "downtime_start", "downtime_end", "total_downtime_hours"])
    return columns, data
