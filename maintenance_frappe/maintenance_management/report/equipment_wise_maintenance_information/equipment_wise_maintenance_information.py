import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Equipment ID / Code"), "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 140},
		{"label": _("Equipment Name"), "fieldname": "equipment_name", "fieldtype": "Data", "width": 180},
		{"label": _("Equipment Category"), "fieldname": "equipment_category", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Total Requests"), "fieldname": "total_requests", "fieldtype": "Int", "width": 120},
		{"label": _("Open Requests"), "fieldname": "open_requests", "fieldtype": "Int", "width": 120},
		{"label": _("Resolved/Closed"), "fieldname": "resolved_requests", "fieldtype": "Int", "width": 130},
		{"label": _("Total Parts Cost"), "fieldname": "total_parts_cost", "fieldtype": "Currency", "width": 130},
		{"label": _("Total Labour Cost"), "fieldname": "total_labour_cost", "fieldtype": "Currency", "width": 130},
		{"label": _("Total Maintenance Cost"), "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 160}
	]

	conditions = ""
	if filters and filters.get("equipment"):
		conditions += f" WHERE mr.equipment = {frappe.db.escape(filters.get('equipment'))}"

	query = f"""
		SELECT
			COALESCE(mr.equipment, 'Unlinked') as equipment,
			COALESCE(mr.equipment_name, e.equipment_name, 'Unknown') as equipment_name,
			mr.equipment_category,
			mr.department,
			COUNT(mr.name) as total_requests,
			SUM(CASE WHEN mr.status IN ('Submitted', 'Pending Approval', 'Approved', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) as open_requests,
			SUM(CASE WHEN mr.status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved_requests,
			SUM(COALESCE(mr.total_parts_cost, 0)) as total_parts_cost,
			SUM(COALESCE(mr.total_labour_cost, 0)) as total_labour_cost,
			SUM(COALESCE(mr.total_maintenance_cost, 0)) as total_maintenance_cost
		FROM `tabMaintenance Request` mr
		LEFT JOIN `tabEquipment` e ON mr.equipment = e.name
		{conditions}
		GROUP BY mr.equipment, mr.equipment_name, mr.equipment_category, mr.department
		ORDER BY total_maintenance_cost DESC
	"""

	data = frappe.db.sql(query, as_dict=True)
	return columns, data
