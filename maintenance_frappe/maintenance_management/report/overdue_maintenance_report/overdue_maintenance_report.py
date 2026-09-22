import frappe
from frappe import _
from frappe.utils import date_diff, today

def execute(filters=None):
	columns = [
		{"label": _("Request ID"), "fieldname": "name", "fieldtype": "Link", "options": "Maintenance Request", "width": 140},
		{"label": _("Title"), "fieldname": "title", "fieldtype": "Data", "width": 200},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 130},
		{"label": _("Equipment"), "fieldname": "equipment_name", "fieldtype": "Data", "width": 150},
		{"label": _("Category"), "fieldname": "equipment_category", "fieldtype": "Data", "width": 140},
		{"label": _("Priority"), "fieldname": "priority", "fieldtype": "Data", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Request Date"), "fieldname": "request_date", "fieldtype": "Date", "width": 110},
		{"label": _("Expected Completion"), "fieldname": "estimated_completion_time", "fieldtype": "Date", "width": 140},
		{"label": _("Days Overdue"), "fieldname": "overdue_days", "fieldtype": "Int", "width": 110},
	]

	current_date = today()
	conditions = {"status": ["not in", ["Resolved", "Closed", "Rejected"]]}

	if filters:
		if filters.get("equipment_category"):
			conditions["equipment_category"] = filters.get("equipment_category")
		if filters.get("priority"):
			conditions["priority"] = filters.get("priority")

	requests = frappe.get_all(
		"Maintenance Request",
		filters=conditions,
		fields=[
			"name",
			"title",
			"employee_name",
			"department",
			"equipment_name",
			"equipment_category",
			"priority",
			"status",
			"request_date",
			"estimated_completion_time"
		],
		order_by="request_date asc"
	)

	data = []
	for req in requests:
		target_date = req.get("estimated_completion_time") or req.get("request_date")
		if target_date:
			target_date_str = str(target_date)[:10]
			days_overdue = date_diff(current_date, target_date_str)
			if days_overdue >= 0:
				req["overdue_days"] = days_overdue
				data.append(req)

	return columns, data
