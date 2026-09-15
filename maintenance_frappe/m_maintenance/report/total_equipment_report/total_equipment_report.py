import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{"label": _("Equipment ID"), "fieldname": "equipment_id", "fieldtype": "Link", "options": "Equipment", "width": 140},
		{"label": _("Equipment Name"), "fieldname": "equipment_name", "fieldtype": "Data", "width": 180},
		{"label": _("Equipment Category"), "fieldname": "equipment_category", "fieldtype": "Link", "options": "Equipment Category", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Criticality"), "fieldname": "criticality", "fieldtype": "Data", "width": 100},
		{"label": _("Maintenance Type"), "fieldname": "maintenance_type", "fieldtype": "Data", "width": 130},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": _("Unit"), "fieldname": "unit", "fieldtype": "Data", "width": 120},
		{"label": _("Serial Number"), "fieldname": "serial_number", "fieldtype": "Data", "width": 140}
	]

	conditions = {}
	if filters:
		if filters.get("equipment_category"):
			conditions["equipment_category"] = filters["equipment_category"]
		if filters.get("status"):
			conditions["status"] = filters["status"]
		if filters.get("department"):
			conditions["department"] = filters["department"]

	data = frappe.get_all(
		"Equipment",
		filters=conditions,
		fields=[
			"equipment_id", "equipment_name", "equipment_category",
			"status", "criticality", "maintenance_type",
			"department", "unit", "serial_number"
		],
		order_by="creation desc"
	)

	return columns, data
