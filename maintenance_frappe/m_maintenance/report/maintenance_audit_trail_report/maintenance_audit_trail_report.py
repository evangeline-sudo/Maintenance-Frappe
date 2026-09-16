import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Request ID", "fieldname": "parent", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
        {"label": "Date Time", "fieldname": "date_time", "fieldtype": "Datetime", "width": 150},
        {"label": "Changed By", "fieldname": "changed_by", "fieldtype": "Data", "width": 140},
        {"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 200}
    ]
    data = frappe.get_all("Maintenance Status History", fields=["parent", "status", "date_time", "changed_by", "notes"], order_by="date_time desc")
    return columns, data
