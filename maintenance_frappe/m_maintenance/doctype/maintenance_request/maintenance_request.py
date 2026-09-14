import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime


class MaintenanceRequest(Document):
	"""
	Maintenance Request DocType
	Handles the complete lifecycle of maintenance requests from submission to closure.
	Supports both Organizational Asset Maintenance and Non-Organizational Asset Maintenance
	across IT, Electrical, Vehicle, Machine, Furniture, Facility, Medical Equipment, etc.
	"""

	def before_insert(self):
		"""Set default values before insert"""
		self.created_on = datetime.now()
		self.created_by = frappe.session.user
		if not self.ownership_type:
			self.ownership_type = "Organizational Asset"

	def on_submit(self):
		"""On submit, add initial status history entry"""
		self.add_status_history("Submitted", f"Request submitted for {self.ownership_type}")
		# Auto-determine if Unit Head approval is required
		self.check_approval_requirement()

	def on_update(self):
		"""On update, track modifications"""
		self.modified_on = datetime.now()
		self.modified_by = frappe.session.user

	def validate(self):
		"""Validate the document"""
		self.validate_employee()
		self.validate_maintenance_type()
		self.validate_ownership_type()
		self.validate_asset_details()
		self.calculate_total_costs()

	def validate_employee(self):
		"""Validate that employee exists and get department"""
		if self.employee:
			emp = frappe.get_doc("Employee", self.employee)
			self.employee_name = emp.employee_name
			self.department = emp.department

	def validate_maintenance_type(self):
		"""Validate maintenance type and equipment category are selected"""
		if not self.maintenance_type:
			frappe.throw(_("Maintenance Type is mandatory"))
		if not self.equipment_category:
			frappe.throw(_("Equipment Category is mandatory"))

	def validate_ownership_type(self):
		"""Validate fields based on Organizational vs Non-Organizational Asset"""
		if self.ownership_type == "Non-Organizational Asset":
			if not self.external_ownership_type:
				frappe.throw(_("External Ownership Type is mandatory for Non-Organizational Asset maintenance"))
			if not self.external_owner_name:
				frappe.throw(_("External Owner / Provider Name is mandatory for Non-Organizational Asset maintenance"))
		elif self.ownership_type == "Organizational Asset":
			# Clear non-organizational specific fields if switched to organizational
			pass

	def validate_asset_details(self):
		"""Validate asset if provided for organizational equipment"""
		if self.ownership_type == "Organizational Asset" and self.asset:
			try:
				asset = frappe.get_doc("Asset", self.asset)
				self.equipment_name = asset.asset_name
				self.equipment_serial = asset.name
			except frappe.DoesNotExistError:
				frappe.throw(_("Asset {0} does not exist").format(self.asset))

	def check_approval_requirement(self):
		"""
		Determine if Unit Head approval is required based on:
		- Unit
		- Department
		- Category
		- Priority
		"""
		approval_required = frappe.db.get_value(
			"Maintenance Approval Rule",
			{
				"unit": self.unit or "",
				"department": self.department or "",
				"category": self.category or "",
				"priority": self.priority,
				"disabled": 0
			}
		)

		if approval_required:
			self.update_status("Pending Approval", "Awaiting Unit Head approval")
			self.approval_status = "Pending"
			if self.unit_head:
				self.create_approval_todo()
		else:
			self.update_status("Approved", "Auto-approved")
			self.approval_status = "Approved"
			self.approval_date = datetime.now()

	def update_status(self, new_status, reason=""):
		"""Update request status and add to history"""
		if self.status != new_status:
			self.status = new_status
			self.add_status_history(new_status, reason)

	def add_status_history(self, status, notes=""):
		"""Add entry to status history table"""
		self.append("status_history", {
			"status": status,
			"date_time": datetime.now(),
			"changed_by": frappe.session.user,
			"notes": notes
		})

	def create_approval_todo(self):
		"""Create a ToDo for Unit Head approval"""
		todo = frappe.get_doc({
			"doctype": "ToDo",
			"owner": self.unit_head,
			"description": f"Approval required for Maintenance Request {self.name}",
			"reference_type": "Maintenance Request",
			"reference_name": self.name,
			"priority": "High" if self.priority == "Critical" else "Medium"
		})
		todo.insert(ignore_permissions=True)

	def approve_request(self, approval_notes=""):
		"""Unit Head approves the maintenance request"""
		if self.approval_status != "Pending":
			frappe.throw(_("Only pending requests can be approved"))

		self.approval_status = "Approved"
		self.approval_date = datetime.now()
		self.approval_notes = approval_notes
		self.update_status("Approved", f"Approved by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} approved").format(self.name))

	def reject_request(self, approval_notes=""):
		"""Unit Head rejects the maintenance request"""
		if self.approval_status != "Pending":
			frappe.throw(_("Only pending requests can be rejected"))

		self.approval_status = "Rejected"
		self.approval_notes = approval_notes
		self.update_status("Submitted", f"Rejected by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} rejected").format(self.name))

	def assign_to_technician(self, technician, notes=""):
		"""Admin assigns the request to a technician"""
		if self.status not in ["Approved", "Assigned"]:
			frappe.throw(_("Request must be approved before assignment"))

		self.assigned_to = technician
		self.assigned_date = datetime.now()
		self.update_status("Assigned", f"Assigned to technician {technician}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} assigned to {1}").format(self.name, technician))

	def start_work(self):
		"""Technician starts work on the request"""
		if self.status != "Assigned":
			frappe.throw(_("Request must be assigned before starting work"))

		self.update_status("In Progress", f"Work started by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Work started on Maintenance Request {0}").format(self.name))

	def save_diagnosis(self, diagnosis_notes, estimated_cost=0, estimated_completion_time=None):
		"""Technician records diagnosis findings and estimates"""
		self.diagnosis_notes = diagnosis_notes
		self.estimated_cost = estimated_cost
		if estimated_completion_time:
			self.estimated_completion_time = estimated_completion_time
		self.add_status_history(self.status, f"Diagnosis updated by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Diagnosis details saved for Maintenance Request {0}").format(self.name))

	def mark_resolved(self, resolution_notes="", root_cause=""):
		"""Technician marks the request as resolved"""
		if self.status != "In Progress":
			frappe.throw(_("Request must be in progress to mark as resolved"))

		self.resolution_date = datetime.now()
		self.resolution_notes = resolution_notes
		self.root_cause = root_cause
		self.update_status("Resolved", f"Marked as resolved by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} marked as resolved").format(self.name))

	def verify_request(self, verification_status, feedback="", verified_by=None):
		"""Supervisor or Requester verifies the completed maintenance work"""
		if self.status != "Resolved":
			frappe.throw(_("Request must be resolved before verification"))

		self.verification_status = verification_status
		self.verification_feedback = feedback
		self.verification_date = datetime.now()
		self.verified_by = verified_by or frappe.session.user

		if verification_status == "Rework Required":
			self.update_status("In Progress", f"Rework requested during verification by {self.verified_by}")
		else:
			self.add_status_history(self.status, f"Verified ({verification_status}) by {self.verified_by}")

		self.save()
		frappe.msgprint(_("Verification status updated for Maintenance Request {0}").format(self.name))

	def close_request(self, closing_remarks="", verified_by=""):
		"""Supervisor/Unit Head closes the request"""
		if self.status != "Resolved":
			frappe.throw(_("Request must be resolved before closure"))

		self.closed_date = datetime.now()
		self.closing_remarks = closing_remarks
		if verified_by:
			self.verified_by = verified_by
		if not self.verification_status or self.verification_status == "Pending":
			self.verification_status = "Verified"
			self.verification_date = datetime.now()

		self.update_status("Closed", f"Closed and verified by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} closed").format(self.name))

	def add_work_log(self, technician, description, duration_minutes=0, hourly_rate=0, status="In Progress"):
		"""Add a work log entry with labour cost calculation"""
		duration_minutes = int(duration_minutes or 0)
		hourly_rate = float(hourly_rate or 0)
		labour_amount = (duration_minutes / 60.0) * hourly_rate if duration_minutes and hourly_rate else 0.0

		self.append("work_logs", {
			"date_time": datetime.now(),
			"technician": technician,
			"description": description,
			"duration_minutes": duration_minutes,
			"hourly_rate": hourly_rate,
			"labour_amount": labour_amount,
			"status": status
		})
		self.calculate_total_costs()
		self.save()
		frappe.msgprint(_("Work log added to Maintenance Request {0}").format(self.name))

	def add_parts_used(self, item, quantity, uom="", rate=0, notes=""):
		"""Add parts used entry"""
		if not frappe.db.exists("Item", item):
			frappe.throw(_("Item {0} does not exist").format(item))

		item_doc = frappe.get_doc("Item", item)
		quantity = float(quantity or 0)
		rate = float(rate or 0)
		amount = quantity * rate

		self.append("parts_used", {
			"item": item,
			"item_name": item_doc.item_name,
			"quantity": quantity,
			"uom": uom or item_doc.stock_uom,
			"rate": rate,
			"amount": amount,
			"notes": notes
		})
		self.calculate_total_costs()
		self.save()
		frappe.msgprint(_("Parts used added to Maintenance Request {0}").format(self.name))

	def calculate_total_costs(self):
		"""Calculate and update total parts, labour, and maintenance costs"""
		self.total_parts_cost = self.get_total_parts_cost()
		self.total_labour_cost = self.get_total_labour_cost()
		self.total_maintenance_cost = self.total_parts_cost + self.total_labour_cost

	def get_total_parts_cost(self):
		"""Calculate total cost of parts used"""
		return sum([flt(line.amount) for line in self.parts_used])

	def get_total_labour_cost(self):
		"""Calculate total labour cost from work logs"""
		total = 0.0
		for line in self.work_logs:
			if getattr(line, "labour_amount", 0):
				total += flt(line.labour_amount)
			elif getattr(line, "duration_minutes", 0) and getattr(line, "hourly_rate", 0):
				total += (flt(line.duration_minutes) / 60.0) * flt(line.hourly_rate)
		return total

	def get_total_work_hours(self):
		"""Calculate total work hours from work logs"""
		total_minutes = sum([flt(line.duration_minutes) for line in self.work_logs])
		return total_minutes / 60.0 if total_minutes else 0.0


def flt(val, default=0.0):
	"""Helper float conversion"""
	try:
		return float(val or 0.0)
	except (ValueError, TypeError):
		return default
