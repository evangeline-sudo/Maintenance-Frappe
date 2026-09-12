import frappe


def get_dashboard_data(data):
	"""
	Generate dashboard data for Maintenance Request
	Shows counts by status, priority, and type
	"""
	return {
		"total_count": frappe.db.count("Maintenance Request"),
		"status_breakdown": frappe.get_list(
			"Maintenance Request",
			fields=["status", "count(*) as count"],
			group_by="status",
			as_list=True
		),
		"priority_breakdown": frappe.get_list(
			"Maintenance Request",
			fields=["priority", "count(*) as count"],
			group_by="priority",
			as_list=True
		),
		"type_breakdown": frappe.get_list(
			"Maintenance Request",
			fields=["maintenance_type", "count(*) as count"],
			group_by="maintenance_type",
			as_list=True
		),
		"pending_approval": frappe.db.count(
			"Maintenance Request",
			{"approval_status": "Pending"}
		),
		"in_progress": frappe.db.count(
			"Maintenance Request",
			{"status": "In Progress"}
		),
		"recent_requests": frappe.get_list(
			"Maintenance Request",
			fields=["name", "title", "status", "priority", "employee"],
			order_by="creation desc",
			limit_page_length=5
		)
	}
