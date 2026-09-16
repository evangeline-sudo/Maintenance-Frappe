import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
		{"label": _("Total Count"), "fieldname": "count", "fieldtype": "Int", "width": 120},
		{"label": _("Estimated Total Cost"), "fieldname": "total_estimated_cost", "fieldtype": "Currency", "width": 160},
		{"label": _("Total Parts Cost"), "fieldname": "total_parts_cost", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Labour Cost"), "fieldname": "total_labour_cost", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Actual Cost"), "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 160}
	]

	conditions = ""
	if filters and filters.get("department"):
		conditions += f" WHERE department = {frappe.db.escape(filters.get('department'))}"

	query = f"""
		SELECT
			status,
			COUNT(name) as count,
			SUM(COALESCE(estimated_cost, 0)) as total_estimated_cost,
			SUM(COALESCE(total_parts_cost, 0)) as total_parts_cost,
			SUM(COALESCE(total_labour_cost, 0)) as total_labour_cost,
			SUM(COALESCE(total_maintenance_cost, 0)) as total_maintenance_cost
		FROM `tabMaintenance Request`
		{conditions}
		GROUP BY status
		ORDER BY FIELD(status, 'Submitted', 'Pending Approval', 'Approved', 'Assigned', 'In Progress', 'Resolved', 'Closed')
	"""

	data = frappe.db.sql(query, as_dict=True)
	return columns, data
