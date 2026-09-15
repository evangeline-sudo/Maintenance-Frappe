import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Contract ID", "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Contract", "width": 140},
        {"label": "Vendor", "fieldname": "vendor", "fieldtype": "Link", "options": "Maintenance Vendor", "width": 150},
        {"label": "Type", "fieldname": "contract_type", "fieldtype": "Data", "width": 130},
        {"label": "End Date", "fieldname": "end_date", "fieldtype": "Date", "width": 130},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110}
    ]
    data = frappe.get_all("Maintenance Contract", fields=["name", "vendor", "contract_type", "end_date", "status"], order_by="end_date asc")
    return columns, data
