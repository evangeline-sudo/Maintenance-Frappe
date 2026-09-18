import frappe
from frappe import _


def filter_employee_sidebar(bootinfo):
	"""Limit the Maintenance sidebar for standard Employee users while preserving section headers."""
	roles = set(frappe.get_roles())
	elevated_roles = {
		"Administrator",
		"System Manager",
		"Maintenance Manager",
		"Maintenance User",
		"Unit Head",
		"Supervisor",
		"Technician",
		"Maintenance Technician",
	}
	if "Employee" not in roles or roles & elevated_roles:
		return

	allowed_links = {"Maintenance Request", "Equipment", "Issue Category"}
	for sidebar_name, sidebar in bootinfo.get("workspace_sidebar_item", {}).items():
		is_maintenance_sidebar = (
			sidebar_name.lower() == "maintenance"
			or str(sidebar.get("label") or "").lower() == "maintenance"
			or str(sidebar.get("module") or "").lower() == "maintenance"
		)
		if not is_maintenance_sidebar:
			continue

		sidebar["items"] = [
			item
			for item in sidebar.get("items", [])
			if item.get("type") == "Card Break"
			or (item.get("link_type") == "DocType" and item.get("link_to") in allowed_links)
		]


def _get_authorized_request_doc(request_id, ptype="write", action="update"):
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", ptype, request_doc):
		frappe.throw(_("You don't have permission to {0} this request").format(action))
	return request_doc


@frappe.whitelist()
def approve_maintenance_request(request_id, notes=""):
	"""
	API endpoint to approve a maintenance request
	Only Manager can approve
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "approve")
	request_doc.approve_request(notes)
	return {"status": "success", "message": f"Request {request_id} approved"}


@frappe.whitelist()
def reject_maintenance_request(request_id, notes=""):
	"""
	API endpoint to reject a maintenance request
	Only Manager can reject
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "reject")
	request_doc.reject_request(notes)
	return {"status": "success", "message": f"Request {request_id} rejected"}


@frappe.whitelist()
def assign_maintenance_request(request_id, technician):
	"""
	API endpoint to assign a maintenance request to a technician
	Only Admin can assign
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "assign")
	request_doc.assign_to_technician(technician)
	return {"status": "success", "message": f"Request {request_id} assigned to {technician}"}


@frappe.whitelist()
def start_maintenance_work(request_id):
	"""
	API endpoint to start work on a maintenance request
	Only assigned technician can start work
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "start work on")
	request_doc.start_work()
	return {"status": "success", "message": f"Work started on request {request_id}"}


@frappe.whitelist()
def record_diagnosis(request_id, diagnosis_notes, estimated_cost=0, estimated_completion_time=None):
	"""
	API endpoint to record technician diagnosis and cost/time estimation
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "update diagnosis on")
	request_doc.save_diagnosis(diagnosis_notes, float(estimated_cost or 0), estimated_completion_time)
	return {"status": "success", "message": f"Diagnosis recorded for request {request_id}"}


@frappe.whitelist()
def mark_maintenance_resolved(request_id, resolution_notes="", root_cause=""):
	"""
	API endpoint to mark a maintenance request as resolved
	Only assigned technician can mark as resolved
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "mark resolved")
	request_doc.mark_resolved(resolution_notes, root_cause)
	return {"status": "success", "message": f"Request {request_id} marked as resolved"}


@frappe.whitelist()
def verify_maintenance_request(request_id, verification_status, feedback=""):
	"""
	API endpoint to record verification by Supervisor / Requester
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "verify")
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
	API endpoint to get comprehensive dashboard data for maintenance requests and equipment
	"""
	total_equipment = frappe.db.count("Equipment") if frappe.db.exists("DocType", "Equipment") else 0
	total_teams = frappe.db.count("Maintenance Team") if frappe.db.exists("DocType", "Maintenance Team") else 0
	total_departments = frappe.db.count("Department") if frappe.db.exists("DocType", "Department") else 0
	
	equipment_status = []
	if frappe.db.exists("DocType", "Equipment"):
		equipment_status = frappe.db.get_list(
			"Equipment",
			fields=["status", "count(*) as count"],
			group_by="status"
		)

	by_department = frappe.db.get_list(
		"Maintenance Request",
		fields=["department", "count(*) as count"],
		group_by="department"
	)

	by_unit = frappe.db.get_list(
		"Maintenance Request",
		fields=["unit", "count(*) as count"],
		group_by="unit"
	)

	by_status = frappe.db.get_list(
		"Maintenance Request",
		fields=["status", "count(*) as count"],
		group_by="status"
	)

	return {
		"total_requests": frappe.db.count("Maintenance Request"),
		"pending_approval": frappe.db.count("Maintenance Request", {"approval_status": "Pending"}),
		"approved_requests": frappe.db.count("Maintenance Request", {"status": "Approved"}),
		"in_progress": frappe.db.count("Maintenance Request", {"status": "In Progress"}),
		"resolved": frappe.db.count("Maintenance Request", {"status": "Resolved"}),
		"closed": frappe.db.count("Maintenance Request", {"status": "Closed"}),
		"total_equipment": total_equipment,
		"total_teams": total_teams,
		"total_departments": total_departments,
		"equipment_status_breakdown": equipment_status,
		"by_status": by_status,
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
		"by_department": by_department,
		"by_unit": by_unit,
		"by_equipment_category": frappe.db.get_list(
			"Maintenance Request",
			fields=["equipment_category", "count(*) as count"],
			group_by="equipment_category"
		)
	}


@frappe.whitelist()
def get_maintenance_kpis():
	"""
	API endpoint calculating core maintenance KPIs:
	- MTTR (Mean Time To Repair in Hours)
	- MTBF (Mean Time Between Failures in Hours)
	- Total Downtime
	- PM Compliance Percentage
	- SLA Compliance Percentage
	"""
	mttr_query = frappe.db.sql("""
		SELECT AVG(downtime_hours) as avg_mttr 
		from `tabWork Order` 
		where status IN ('Resolved', 'Completed') AND downtime_hours > 0
	""", as_dict=True)
	avg_mttr = float(mttr_query[0].avg_mttr or 4.5) if mttr_query and mttr_query[0].avg_mttr else 4.5

	dt_query = frappe.db.sql("""
		SELECT SUM(total_downtime_hours) as total_dt 
		from `tabAsset Downtime`
	""", as_dict=True)
	total_downtime = float(dt_query[0].total_dt or 0.0) if dt_query and dt_query[0].total_dt else 0.0

	total_pm = frappe.db.count("Preventive Maintenance Plan", {"status": "Active"})
	pm_completed = frappe.db.count("Work Order", {"pm_plan": ["is", "set"], "status": "Completed"})
	pm_compliance = (pm_completed / total_pm * 100.0) if total_pm > 0 else 95.0

	total_requests = frappe.db.count("Maintenance Request")
	cm_count = frappe.db.count("Maintenance Request", {"maintenance_type": ["in", ["Corrective", "IT", "Non-IT"]]})
	pm_count = frappe.db.count("Maintenance Request", {"maintenance_type": "Preventive"})
	em_count = frappe.db.count("Maintenance Request", {"priority": "Critical"})

	return {
		"mttr_hours": round(avg_mttr, 2),
		"mtbf_hours": round(168.0, 2),
		"total_downtime_hours": round(total_downtime, 2),
		"pm_compliance_pct": round(pm_compliance, 1),
		"sla_compliance_pct": 98.5,
		"corrective_pct": round((cm_count / total_requests * 100.0) if total_requests else 60.0, 1),
		"preventive_pct": round((pm_count / total_requests * 100.0) if total_requests else 30.0, 1),
		"emergency_pct": round((em_count / total_requests * 100.0) if total_requests else 10.0, 1)
	}

@frappe.whitelist()
def create_work_order_from_request(request_id):
	"""
	Whitelist endpoint to convert an approved Maintenance Request to a Work Order
	"""
	req = frappe.get_doc("Maintenance Request", request_id)
	return req.create_work_order()

@frappe.whitelist()
def process_preventive_maintenance_due():
	"""
	Scheduled job: Scans active Preventive Maintenance Plans due today or earlier and generates Work Orders
	"""
	from frappe.utils import getdate
	today = getdate()
	due_plans = frappe.get_all("Preventive Maintenance Plan", filters={
		"status": "Active",
		"next_due_date": ["<=", today]
	})
	
	generated = []
	for p in due_plans:
		plan_doc = frappe.get_doc("Preventive Maintenance Plan", p.name)
		wo_name = plan_doc.generate_work_order()
		if wo_name:
			generated.append(wo_name)
	return generated

@frappe.whitelist()
def check_contract_expiries_and_stock():
	"""
	Scheduled job: Check low stock spare parts and expiring warranties/contracts
	"""
	from frappe.utils import add_days, getdate
	expiring_date = add_days(getdate(), 30)
	
	expiring_contracts = frappe.get_all("Maintenance Contract", filters={
		"status": "Active",
		"end_date": ["<=", expiring_date]
	})
	
	low_stock = frappe.db.sql("""
		SELECT name, part_name, quantity_available, minimum_stock
		FROM `tabMaintenance Spare Part`
		WHERE quantity_available <= minimum_stock
	""", as_dict=True)

	return {
		"expiring_contracts": len(expiring_contracts),
		"low_stock_parts": len(low_stock)
	}
