import frappe
from frappe import _


@frappe.whitelist()
def approve_maintenance_request(request_id, notes=""):
	"""
	API endpoint to approve a maintenance request
	Only Unit Head can approve
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to approve this request"))

	request_doc.approve_request(notes)
	return {"status": "success", "message": f"Request {request_id} approved"}


@frappe.whitelist()
def reject_maintenance_request(request_id, notes=""):
	"""
	API endpoint to reject a maintenance request
	Only Unit Head can reject
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to reject this request"))

	request_doc.reject_request(notes)
	return {"status": "success", "message": f"Request {request_id} rejected"}


@frappe.whitelist()
def assign_maintenance_request(request_id, technician):
	"""
	API endpoint to assign a maintenance request to a technician
	Only Admin can assign
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to assign this request"))

	request_doc.assign_to_technician(technician)
	return {"status": "success", "message": f"Request {request_id} assigned to {technician}"}


@frappe.whitelist()
def start_maintenance_work(request_id):
	"""
	API endpoint to start work on a maintenance request
	Only assigned technician can start work
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to start work on this request"))

	request_doc.start_work()
	return {"status": "success", "message": f"Work started on request {request_id}"}


@frappe.whitelist()
def record_diagnosis(request_id, diagnosis_notes, estimated_cost=0, estimated_completion_time=None):
	"""
	API endpoint to record technician diagnosis and cost/time estimation
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to update diagnosis on this request"))

	request_doc.save_diagnosis(diagnosis_notes, float(estimated_cost or 0), estimated_completion_time)
	return {"status": "success", "message": f"Diagnosis recorded for request {request_id}"}


@frappe.whitelist()
def mark_maintenance_resolved(request_id, resolution_notes="", root_cause=""):
	"""
	API endpoint to mark a maintenance request as resolved
	Only assigned technician can mark as resolved
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to mark this request as resolved"))

	request_doc.mark_resolved(resolution_notes, root_cause)
	return {"status": "success", "message": f"Request {request_id} marked as resolved"}


@frappe.whitelist()
def verify_maintenance_request(request_id, verification_status, feedback=""):
	"""
	API endpoint to record verification by Supervisor / Requester
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to verify this request"))

	request_doc.verify_request(verification_status, feedback, frappe.session.user)
	return {"status": "success", "message": f"Verification saved for request {request_id}"}


@frappe.whitelist()
def close_maintenance_request(request_id, closing_remarks="", verified_by=""):
	"""
	API endpoint to close a maintenance request
	Only Supervisor or Unit Head can close
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to close this request"))

	request_doc.close_request(closing_remarks, verified_by)
	return {"status": "success", "message": f"Request {request_id} closed"}


@frappe.whitelist()
def add_work_log(request_id, technician, description, duration_minutes=0, hourly_rate=0, status="In Progress"):
	"""
	API endpoint to add a work log entry with hourly rate & labour calculation
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to add work log to this request"))

	request_doc.add_work_log(
		technician, description, int(duration_minutes or 0), float(hourly_rate or 0), status
	)
	return {"status": "success", "message": f"Work log added to request {request_id}"}


@frappe.whitelist()
def add_parts_used(request_id, item, quantity, uom="", rate=0, notes=""):
	"""
	API endpoint to add parts used entry
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to add parts to this request"))

	request_doc.add_parts_used(item, float(quantity), uom, float(rate), notes)
	return {"status": "success", "message": f"Parts added to request {request_id}"}


@frappe.whitelist()
def get_maintenance_requests(filters=None, limit_start=0, limit_page_length=20):
	"""
	API endpoint to get filtered maintenance requests
	Supports status, priority, maintenance_type, ownership_type, equipment_category, employee, assigned_to filters
	"""
	filters = filters or {}

	return frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=[
			"name", "title", "status", "priority", "maintenance_type",
			"ownership_type", "equipment_category", "external_ownership_type",
			"employee", "assigned_to", "creation", "total_maintenance_cost"
		],
		order_by="creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length)
	)


@frappe.whitelist()
def get_maintenance_dashboard_data():
	"""
	API endpoint to get comprehensive dashboard data for maintenance requests
	"""
	return {
		"total_requests": frappe.db.count("Maintenance Request"),
		"pending_approval": frappe.db.count("Maintenance Request", {"approval_status": "Pending"}),
		"in_progress": frappe.db.count("Maintenance Request", {"status": "In Progress"}),
		"resolved": frappe.db.count("Maintenance Request", {"status": "Resolved"}),
		"closed": frappe.db.count("Maintenance Request", {"status": "Closed"}),
		"organizational_count": frappe.db.count("Maintenance Request", {"ownership_type": "Organizational Asset"}),
		"non_organizational_count": frappe.db.count("Maintenance Request", {"ownership_type": "Non-Organizational Asset"}),
		"by_priority": frappe.db.get_list(
			"Maintenance Request",
			fields=["priority", "count(*) as count"],
			group_by="priority"
		),
		"by_type": frappe.db.get_list(
			"Maintenance Request",
			fields=["maintenance_type", "count(*) as count"],
			group_by="maintenance_type"
		),
		"by_ownership": frappe.db.get_list(
			"Maintenance Request",
			fields=["ownership_type", "count(*) as count"],
			group_by="ownership_type"
		),
		"by_equipment_category": frappe.db.get_list(
			"Maintenance Request",
			fields=["equipment_category", "count(*) as count"],
			group_by="equipment_category"
		)
	}
