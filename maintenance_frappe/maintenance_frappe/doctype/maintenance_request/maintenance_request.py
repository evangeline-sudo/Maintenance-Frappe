# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime, time_diff_in_hours


class MaintenanceRequest(Document):
	def before_insert(self):
		self.evaluate_approval_configuration()
		self.record_initial_history()

	def validate(self):
		self.validate_equipment()
		self.validate_issue_category()
		self.validate_assignment()
		self.validate_technician_processing()
		self.validate_resolution()
		self.validate_verification_and_closure()
		self.calculate_performance_metrics()
		self.track_status_change()

	def evaluate_approval_configuration(self):
		"""
		Server-side conditional approval rule evaluation.
		Checks active Unit Head Approval Configuration matching request properties.
		"""
		if not self.issue_category:
			return

		# Query active approval configurations
		rules = frappe.get_all(
			"Unit Head Approval Configuration",
			filters={"is_active": 1},
			fields=[
				"name",
				"unit",
				"department",
				"issue_category",
				"priority",
				"approval_required",
				"unit_head",
			],
		)

		matched_rule = None
		# Find most specific rule
		for rule in rules:
			if rule.issue_category and rule.issue_category != self.issue_category:
				continue
			if rule.unit and rule.unit != self.unit:
				continue
			if rule.department and rule.department != self.department:
				continue
			if rule.priority and rule.priority != self.priority:
				continue

			matched_rule = rule
			break

		if matched_rule and matched_rule.approval_required:
			self.approval_required = 1
			self.approval_status = "Pending"
			self.unit_head = matched_rule.unit_head
			self.status = "Pending Approval"
		else:
			self.approval_required = 0
			self.approval_status = "Not Required"
			if self.status == "Submitted" or not self.status:
				self.status = "Approved"

	def validate_equipment(self):
		if self.equipment:
			status = frappe.db.get_value("Equipment", self.equipment, "status")
			if status in ["Retired", "Disposed"]:
				frappe.throw(
					_("Selected Equipment {0} is {1} and cannot be maintained.").format(
						self.equipment, status
					)
				)

	def validate_issue_category(self):
		if self.issue_category:
			is_active = frappe.db.get_value("Issue Category", self.issue_category, "is_active")
			if is_active is not None and not is_active:
				frappe.throw(
					_("Selected Issue Category {0} is inactive.").format(self.issue_category)
				)

	def validate_assignment(self):
		if self.status == "Assigned":
			if not self.assigned_team:
				frappe.throw(_("Assigned Team is required when status is Assigned."))
			if not self.responsible_person:
				frappe.throw(_("Responsible Person is required when status is Assigned."))

		if self.responsible_person:
			rp = frappe.get_doc("Responsible Person", self.responsible_person)
			if not rp.is_active:
				frappe.throw(
					_("Selected Responsible Person {0} is inactive.").format(self.responsible_person)
				)
			if self.assigned_team and rp.maintenance_team != self.assigned_team:
				frappe.throw(
					_("Responsible Person {0} does not belong to the Assigned Team {1}.").format(
						self.responsible_person, self.assigned_team
					)
				)

	def validate_technician_processing(self):
		if self.status == "In Progress":
			if not self.work_start_date:
				self.work_start_date = now_datetime()

	def validate_resolution(self):
		if self.status in ["Resolved", "Closed"]:
			missing_fields = []
			if not self.diagnosis:
				missing_fields.append(_("Diagnosis"))
			if not self.work_details:
				missing_fields.append(_("Work Details"))
			if not self.resolution_type:
				missing_fields.append(_("Resolution Type"))
			if not self.resolution_details:
				missing_fields.append(_("Resolution Details"))

			if missing_fields:
				frappe.throw(
					_("Please fill mandatory resolution fields before resolving: {0}").format(
						", ".join(missing_fields)
					)
				)

			if not self.work_completion_date:
				self.work_completion_date = now_datetime()
			if not self.resolution_date:
				self.resolution_date = now_datetime()

	def validate_verification_and_closure(self):
		if self.verification_status == "Rework Required":
			if not self.verification_remarks:
				frappe.throw(_("Verification Remarks are mandatory when Rework is required."))
			if self.status != "In Progress":
				self.status = "In Progress"
				self.reopen_count = (self.reopen_count or 0) + 1

		if self.status == "Closed":
			if self.verification_status != "Accepted":
				frappe.throw(
					_("Maintenance Request can only be closed when Verification Status is Accepted.")
				)
			if not self.verified_by:
				employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
				if employee:
					self.verified_by = employee
			if not self.verification_date:
				self.verification_date = now_datetime()

		if self.status == "Rejected":
			if not self.approval_remarks:
				frappe.throw(_("Approval Remarks are mandatory when rejecting a request."))

	def calculate_performance_metrics(self):
		start_ref = self.work_start_date or self.assignment_date
		if self.creation and start_ref:
			self.actual_response_time = round(
				time_diff_in_hours(get_datetime(start_ref), get_datetime(self.creation)), 2
			)
		if self.creation and self.work_completion_date:
			self.actual_resolution_time = round(
				time_diff_in_hours(
					get_datetime(self.work_completion_date), get_datetime(self.creation)
				),
				2,
			)

	def record_initial_history(self):
		user_role = "Employee"
		if "System Manager" in frappe.get_roles():
			user_role = "System Manager"
		elif "Maintenance User" in frappe.get_roles():
			user_role = "Admin"

		self.append(
			"status_history",
			{
				"from_status": "",
				"to_status": self.status,
				"status": self.status,
				"changed_by": frappe.session.user,
				"changed_on": now_datetime(),
				"role": user_role,
				"remarks": _("Initial Request Created"),
			},
		)

	def track_status_change(self):
		if self.is_new():
			return

		old_status = frappe.db.get_value("Maintenance Request", self.name, "status")
		if old_status and old_status != self.status:
			user_roles = frappe.get_roles()
			role = "Employee"
			if "System Manager" in user_roles:
				role = "Admin"
			elif "Maintenance User" in user_roles:
				role = "Maintenance User"

			remarks = self.approval_remarks or self.assignment_remarks or self.verification_remarks or self.closure_remarks or ""
			self.append(
				"status_history",
				{
					"from_status": old_status,
					"to_status": self.status,
					"status": self.status,
					"changed_by": frappe.session.user,
					"changed_on": now_datetime(),
					"role": role,
					"remarks": remarks,
				},
			)

	@frappe.whitelist()
	def approve_request(self, remarks=None):
		if self.status != "Pending Approval":
			frappe.throw(_("Only requests in Pending Approval state can be approved."))
		self.approval_status = "Approved"
		self.approval_date = now_datetime()
		if remarks:
			self.approval_remarks = remarks
		self.status = "Approved"
		self.save()
		return True

	@frappe.whitelist()
	def reject_request(self, remarks=None):
		if self.status != "Pending Approval":
			frappe.throw(_("Only requests in Pending Approval state can be rejected."))
		if not remarks and not self.approval_remarks:
			frappe.throw(_("Approval Remarks are required for rejection."))
		self.approval_status = "Rejected"
		self.approval_date = now_datetime()
		if remarks:
			self.approval_remarks = remarks
		self.status = "Rejected"
		self.save()
		return True

	@frappe.whitelist()
	def assign_technician(self, team, technician, expected_date=None, remarks=None):
		self.assigned_team = team
		self.responsible_person = technician
		self.assignment_date = now_datetime()
		if expected_date:
			self.expected_completion_date = expected_date
		if remarks:
			self.assignment_remarks = remarks
		self.status = "Assigned"
		self.save()
		return True

	@frappe.whitelist()
	def start_maintenance_work(self):
		if self.status not in ["Assigned", "Approved"]:
			frappe.throw(_("Maintenance work can only be started for Assigned or Approved requests."))
		self.work_start_date = now_datetime()
		self.status = "In Progress"
		self.save()
		return True

	@frappe.whitelist()
	def resolve_maintenance(
		self,
		resolution_type,
		resolution_details,
		diagnosis,
		work_details,
		failure_cause=None,
		technician_remarks=None,
	):
		self.resolution_type = resolution_type
		self.resolution_details = resolution_details
		self.diagnosis = diagnosis
		self.work_details = work_details
		if failure_cause:
			self.failure_cause = failure_cause
		if technician_remarks:
			self.technician_remarks = technician_remarks
		self.work_completion_date = now_datetime()
		self.resolution_date = now_datetime()
		self.status = "Resolved"
		self.save()
		return True

	@frappe.whitelist()
	def verify_and_close(self, remarks=None):
		if self.status != "Resolved":
			frappe.throw(_("Only Resolved requests can be verified and closed."))
		self.verification_status = "Accepted"
		self.verification_date = now_datetime()
		if remarks:
			self.verification_remarks = remarks
		employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		if employee:
			self.verified_by = employee
		self.status = "Closed"
		self.save()
		return True

	@frappe.whitelist()
	def request_rework(self, remarks):
		if not remarks:
			frappe.throw(_("Verification Remarks are mandatory for requesting rework."))
		self.verification_status = "Rework Required"
		self.verification_remarks = remarks
		self.status = "In Progress"
		self.reopen_count = (self.reopen_count or 0) + 1
		self.save()
		return True

