import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Spare Part", "fieldname": "spare_part", "fieldtype": "Link", "options": "Maintenance Spare Part", "width": 160},
        {"label": "Part Name", "fieldname": "part_name", "fieldtype": "Data", "width": 160},
        {"label": "Total Quantity Used", "fieldname": "total_qty", "fieldtype": "Float", "width": 150},
        {"label": "Total Cost", "fieldname": "total_cost", "fieldtype": "Currency", "width": 140}
    ]
    data = frappe.db.sql("SELECT spare_part, part_name, SUM(quantity) as total_qty, SUM(total_cost) as total_cost FROM `tabWork Order Part` GROUP BY spare_part, part_name", as_dict=True)
    return columns, data
