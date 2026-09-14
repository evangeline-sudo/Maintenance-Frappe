import frappe
from frappe import _
from datetime import datetime, timedelta


def get_pending_approval_requests(unit_head=None):
	"""Get maintenance requests pending approval for a unit head"""
	filters = {"approval_status": "Pending"}
	if unit_head:
		filters["unit_head"] = unit_head

	return frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=["name", "title", "priority", "employee", "department", "ownership_type", "equipment_category"],
		order_by="priority desc"
	)


def get_assigned_requests(technician=None):
	"""Get maintenance requests assigned to a technician"""
	filters = {"status": ["in", ["Assigned", "In Progress"]]}
	if technician:
		filters["assigned_to"] = technician

	return frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=["name", "title", "status", "priority", "assigned_to", "ownership_type", "equipment_category"],
		order_by="priority desc"
	)


def get_requests_by_status(status):
	"""Get maintenance requests filtered by status"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"status": status},
		fields=["name", "title", "priority", "employee", "assigned_to", "ownership_type", "equipment_category"],
		order_by="creation desc"
	)


def get_requests_by_priority(priority):
	"""Get maintenance requests filtered by priority"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"priority": priority},
		fields=["name", "title", "status", "employee", "assigned_to", "ownership_type", "equipment_category"],
		order_by="creation desc"
	)


def get_requests_by_type(maintenance_type):
	"""Get maintenance requests filtered by type"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"maintenance_type": maintenance_type},
		fields=["name", "title", "status", "priority", "employee", "ownership_type", "equipment_category"],
		order_by="creation desc"
	)


def get_requests_by_ownership(ownership_type):
	"""Get maintenance requests filtered by ownership type (Organizational vs Non-Organizational)"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"ownership_type": ownership_type},
		fields=[
			"name", "title", "status", "priority", "equipment_category",
			"external_ownership_type", "external_owner_name", "employee", "assigned_to"
		],
		order_by="creation desc"
	)


def get_requests_by_equipment_category(equipment_category):
	"""Get maintenance requests filtered by equipment category"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"equipment_category": equipment_category},
		fields=["name", "title", "status", "priority", "ownership_type", "employee", "assigned_to"],
		order_by="creation desc"
	)


def get_employee_requests(employee):
	"""Get all maintenance requests submitted by an employee"""
	return frappe.get_list(
		"Maintenance Request",
		filters={"employee": employee},
		fields=["name", "title", "status", "priority", "assigned_to", "creation", "ownership_type", "equipment_category"],
		order_by="creation desc"
	)


def get_overdue_requests(days=7):
	"""Get requests that have been in same status for more than specified days"""
	cutoff_date = datetime.now() - timedelta(days=days)

	requests = frappe.get_list(
		"Maintenance Request",
		filters=[
			["status", "!=", "Closed"],
			["creation", "<", cutoff_date.isoformat()]
		],
		fields=["name", "title", "status", "priority", "employee", "creation", "ownership_type"],
		order_by="priority desc"
	)

	return requests


def get_request_statistics():
	"""Get overall maintenance request statistics"""
	total = frappe.db.count("Maintenance Request")

	stats = {
		"total": total,
		"by_status": {},
		"by_priority": {},
		"by_type": {},
		"by_ownership": {},
		"by_equipment_category": {}
	}

	# Status breakdown
	status_data = frappe.db.get_list(
		"Maintenance Request",
		fields=["status", "count(*) as count"],
		group_by="status"
	)
	for row in status_data:
		stats["by_status"][row.status] = row.count

	# Priority breakdown
	priority_data = frappe.db.get_list(
		"Maintenance Request",
		fields=["priority", "count(*) as count"],
		group_by="priority"
	)
	for row in priority_data:
		stats["by_priority"][row.priority] = row.count

	# Type breakdown
	type_data = frappe.db.get_list(
		"Maintenance Request",
		fields=["maintenance_type", "count(*) as count"],
		group_by="maintenance_type"
	)
	for row in type_data:
		stats["by_type"][row.maintenance_type] = row.count

	# Ownership breakdown
	ownership_data = frappe.db.get_list(
		"Maintenance Request",
		fields=["ownership_type", "count(*) as count"],
		group_by="ownership_type"
	)
	for row in ownership_data:
		stats["by_ownership"][row.ownership_type] = row.count

	# Equipment Category breakdown
	category_data = frappe.db.get_list(
		"Maintenance Request",
		fields=["equipment_category", "count(*) as count"],
		group_by="equipment_category"
	)
	for row in category_data:
		stats["by_equipment_category"][row.equipment_category] = row.count

	return stats


def get_total_maintenance_costs(ownership_type=None):
	"""Calculate total parts, labour, and maintenance costs"""
	filters = {}
	if ownership_type:
		filters["ownership_type"] = ownership_type

	requests = frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=["total_parts_cost", "total_labour_cost", "total_maintenance_cost"]
	)

	total_parts = sum([r.total_parts_cost or 0 for r in requests])
	total_labour = sum([r.total_labour_cost or 0 for r in requests])
	total_cost = sum([r.total_maintenance_cost or 0 for r in requests])

	return {
		"total_parts_cost": total_parts,
		"total_labour_cost": total_labour,
		"total_maintenance_cost": total_cost
	}


def get_resolution_time_average(maintenance_type=None):
	"""Calculate average time from submission to closure"""
	filters = {"status": "Closed", "closed_date": [">", ""]}
	if maintenance_type:
		filters["maintenance_type"] = maintenance_type

	requests = frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=["name", "creation", "closed_date"]
	)

	if not requests:
		return 0

	total_hours = 0
	for req in requests:
		created = frappe.utils.get_datetime(req.creation)
		closed = frappe.utils.get_datetime(req.closed_date)
		hours = (closed - created).total_seconds() / 3600
		total_hours += hours

	return total_hours / len(requests)


def send_approval_notification(request_id):
	"""Send notification to Unit Head for approval"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)

	if not request_doc.unit_head:
		return

	subject = f"Maintenance Request {request_id} - Approval Required"
	message = f"""
	A new maintenance request requires your approval:

	Request: {request_id}
	Title: {request_doc.title}
	Ownership: {request_doc.ownership_type}
	Equipment Category: {request_doc.equipment_category}
	Priority: {request_doc.priority}
	Employee: {request_doc.employee_name}
	Department: {request_doc.department}

	Please review and approve or reject this request.
	"""

	frappe.sendmail(
		recipients=[request_doc.unit_head],
		subject=subject,
		message=message
	)


def send_assignment_notification(request_id):
	"""Send notification to Technician for assignment"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)

	if not request_doc.assigned_to:
		return

	subject = f"Maintenance Request {request_id} - Assigned to You"
	message = f"""
	You have been assigned a new maintenance request:

	Request: {request_id}
	Title: {request_doc.title}
	Ownership: {request_doc.ownership_type}
	Equipment Category: {request_doc.equipment_category}
	Priority: {request_doc.priority}
	Employee: {request_doc.employee_name}
	Department: {request_doc.department}

	Please start work on this request.
	"""

	frappe.sendmail(
		recipients=[request_doc.assigned_to],
		subject=subject,
		message=message
	)


def send_resolution_notification(request_id):
	"""Send notification to Employee that request is resolved"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)

	if not request_doc.employee:
		return

	user_email = frappe.db.get_value("Employee", request_doc.employee, "user_id")

	if not user_email:
		return

	subject = f"Maintenance Request {request_id} - Resolved"
	message = f"""
	Your maintenance request has been resolved:

	Request: {request_id}
	Title: {request_doc.title}
	Resolution Date: {request_doc.resolution_date}

	Resolution Notes:
	{request_doc.resolution_notes}

	Your supervisor will verify and close this request.
	"""

	frappe.sendmail(
		recipients=[user_email],
		subject=subject,
		message=message
	)


def send_closure_notification(request_id):
	"""Send notification to Employee that request is closed"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)

	if not request_doc.employee:
		return

	user_email = frappe.db.get_value("Employee", request_doc.employee, "user_id")

	if not user_email:
		return

	subject = f"Maintenance Request {request_id} - Closed"
	message = f"""
	Your maintenance request has been closed:

	Request: {request_id}
	Title: {request_doc.title}
	Closed Date: {request_doc.closed_date}
	Verified By: {request_doc.verified_by}

	Closing Remarks:
	{request_doc.closing_remarks}

	Thank you for reporting this issue.
	"""

	frappe.sendmail(
		recipients=[user_email],
		subject=subject,
		message=message
	)
