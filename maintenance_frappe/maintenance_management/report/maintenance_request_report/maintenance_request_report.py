import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Request ID"), "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
		{"label": _("Title"), "fieldname": "title", "fieldtype": "Data", "width": 180},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 100},
		{"label": _("Maintenance Type"), "fieldname": "maintenance_type", "fieldtype": "Data", "width": 130},
		{"label": _("Ownership Type"), "fieldname": "ownership_type", "fieldtype": "Data", "width": 150},
		{"label": _("Equipment"), "fieldname": "equipment", "fieldtype": "Link", "options": "Equipment", "width": 140},
		{"label": _("Equipment Name"), "fieldname": "equipment_name", "fieldtype": "Data", "width": 160},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 130},
		{"label": _("Assigned To"), "fieldname": "assigned_to", "fieldtype": "Link", "options": "User", "width": 140},
		{"label": _("Total Cost"), "fieldname": "total_maintenance_cost", "fieldtype": "Currency", "width": 130},
		{"label": _("Created On"), "fieldname": "creation", "fieldtype": "Datetime", "width": 140}
	]

	conditions = {}
	if filters:
		if filters.get("status"):
			conditions["status"] = filters["status"]
		if filters.get("priority"):
			conditions["priority"] = filters["priority"]
		if filters.get("maintenance_type"):
			conditions["maintenance_type"] = filters["maintenance_type"]
		if filters.get("department"):
			conditions["department"] = filters["department"]
		if filters.get("employee"):
			conditions["employee"] = filters["employee"]
		if filters.get("from_date") and filters.get("to_date"):
			conditions["creation"] = ["between", [filters.get("from_date"), filters.get("to_date")]]

	data = frappe.get_all(
		"Maintenance Request",
		filters=conditions,
		fields=[
			"name", "title", "status", "priority", "maintenance_type",
			"ownership_type", "equipment", "equipment_name", "employee",
			"department", "assigned_to", "total_maintenance_cost", "creation"
		],
		order_by="creation desc"
	)

	return columns, data
