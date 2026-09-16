import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime


CATEGORY_MAINTENANCE_TYPE_MAP = {
	"IT Equipment": ["IT"],
	"Electrical Equipment": ["Non-IT"],
	"Vehicle": ["Non-IT"],
	"Machine": ["Non-IT"],
	"Furniture": ["Non-IT"],
	"Building/Facility": ["Non-IT"],
	"Office Equipment": ["Non-IT"],
	"Medical Equipment": ["Professional-Specialized"],
	"Other": ["Non-IT"]
}


class MaintenanceRequest(Document):
	"""
	Maintenance Request DocType
	Handles the complete lifecycle of maintenance requests from submission to closure.
	Supports both Organizational Asset Maintenance and Non-Organizational Asset Maintenance
	across IT, Electrical, Vehicle, Machine, Furniture, Facility, Medical Equipment, etc.
	"""

	def _set_defaults(self):
		super()._set_defaults()
		self.auto_create_issue_category()
		self.auto_handle_equipment()

	def before_insert(self):
		"""Set default values and auto-create linked entities before link validation"""
		if not self.ownership_type:
			self.ownership_type = "Organizational Asset"
		self.auto_create_issue_category()
		self.auto_handle_equipment()

	def on_submit(self):
		"""On submit, add initial status history entry"""
		self.add_status_history("Submitted", f"Request submitted for {self.ownership_type}")
		# Auto-determine if Unit Head approval is required
		self.check_approval_requirement()

	def before_validate(self):
		"""Pre-validation hook: auto-assign default maintenance_type for equipment_category if missing"""
		if getattr(self, "equipment_category", None):
			allowed = CATEGORY_MAINTENANCE_TYPE_MAP.get(self.equipment_category, ["Non-IT"])
			if not getattr(self, "maintenance_type", None):
				self.maintenance_type = allowed[0]

		self.auto_create_issue_category()
		self.auto_handle_equipment()

	def validate(self):
		"""Validate the document"""
		self.validate_employee()
		self.validate_maintenance_type()
		self.validate_ownership_type()
		self.validate_asset_details()
		self.check_approved_status()
		self.calculate_total_costs()

	def auto_create_issue_category(self):
		"""Automatically create Issue Category if it does not exist"""
		if self.issue_category and not frappe.db.exists("Issue Category", self.issue_category):
			eq_cat = self.equipment_category if frappe.db.exists("Equipment Category", self.equipment_category) else None
			issue_cat = frappe.get_doc({
				"doctype": "Issue Category",
				"issue_category_name": self.issue_category,
				"equipment_category": eq_cat,
				"is_active": 1
			})
			issue_cat.insert(ignore_permissions=True)

	def auto_handle_equipment(self):
		"""Automatically create or link Equipment record based on details"""
		if self.equipment and frappe.db.exists("Equipment", self.equipment):
			eq_doc = frappe.get_doc("Equipment", self.equipment)
			if eq_doc.equipment_name:
				self.equipment_name = eq_doc.equipment_name
			if eq_doc.serial_number or eq_doc.equipment_id:
				self.equipment_serial = eq_doc.serial_number or eq_doc.equipment_id
			if getattr(eq_doc, "location", None):
				self.equipment_location = eq_doc.location
				if not getattr(self, "location", None):
					self.location = eq_doc.location
			if getattr(eq_doc, "department", None):
				self.department = eq_doc.department
			if getattr(eq_doc, "unit", None):
				self.unit = eq_doc.unit
			if getattr(eq_doc, "equipment_category", None):
				category_map = {
					"Electrical": "Electrical Equipment",
					"IT": "IT Equipment",
					"Vehicles": "Vehicle",
					"Medical": "Medical Equipment",
					"HVAC": "Building/Facility",
					"Network": "IT Equipment"
				}
				eq_cat = eq_doc.equipment_category
				self.equipment_category = category_map.get(eq_cat, eq_cat if eq_cat in ["IT Equipment", "Electrical Equipment", "Vehicle", "Machine", "Furniture", "Building/Facility", "Medical Equipment", "Office Equipment", "Other"] else "Other")
			if getattr(eq_doc, "maintenance_type", None):
				self.maintenance_type = eq_doc.maintenance_type if eq_doc.maintenance_type in ["IT", "Non-IT", "Professional-Specialized"] else "IT"
			return

		# Check if equipment already exists in DB by serial or name
		existing_eq = None
		eq_serial = getattr(self, "equipment_serial", None)
		eq_name = getattr(self, "equipment_name", None)
		eq_category = getattr(self, "equipment_category", None)
		maint_type = getattr(self, "maintenance_type", None)

		if eq_serial:
			existing_eq = frappe.db.get_value("Equipment", {"serial_number": eq_serial}, "name") \
				or frappe.db.get_value("Equipment", {"equipment_id": eq_serial}, "name")
		if not existing_eq and eq_name:
			existing_eq = frappe.db.get_value("Equipment", {"equipment_name": eq_name, "department": getattr(self, "department", "") or ""}, "name") \
				or frappe.db.get_value("Equipment", {"equipment_name": eq_name}, "name")

		if existing_eq:
			self.equipment = existing_eq
		elif eq_name or eq_serial:
			eq_id = eq_serial or eq_name
			eq_cat = eq_category if eq_category and frappe.db.exists("Equipment Category", eq_category) else None
			if not eq_cat and eq_category:
				try:
					new_eq_cat = frappe.get_doc({
						"doctype": "Equipment Category",
						"category_name": self.equipment_category,
						"is_active": 1
					})
					new_eq_cat.insert(ignore_permissions=True)
					eq_cat = new_eq_cat.name
				except Exception:
					eq_cat = None

			new_eq = frappe.get_doc({
				"doctype": "Equipment",
				"equipment_id": eq_id,
				"equipment_name": self.equipment_name or self.equipment_serial or "Equipment",
				"equipment_category": eq_cat,
				"maintenance_type": self.maintenance_type if self.maintenance_type in ["IT", "Non-IT", "Professional/Specialized"] else "Non-IT",
				"serial_number": self.equipment_serial,
				"department": getattr(self, "department", None),
				"unit": getattr(self, "unit", None),
				"status": "Active"
			})
			new_eq.insert(ignore_permissions=True)
			self.equipment = new_eq.name

	def check_approved_status(self):
		"""Ensure status is set to Approved when approval_status is Approved"""
		if hasattr(self, "status") and self.approval_status == "Approved" and self.status in ["Submitted", "Pending Approval"]:
			self.status = "Approved"

	def create_work_order(self):
		wo_maint_type = self.maintenance_type if self.maintenance_type in ["Corrective", "Preventive", "Predictive", "Emergency", "Routine", "Breakdown", "Inspection", "Calibration", "Servicing"] else "Corrective"
		wo = frappe.get_doc({
			"doctype": "Work Order",
			"maintenance_request": self.name,
			"equipment": self.equipment,
			"equipment_name": self.equipment_name,
			"department": self.department,
			"location": self.location,
			"maintenance_type": wo_maint_type,
			"priority": self.priority,
			"assigned_team": getattr(self, "assigned_team", None),
			"assigned_technician": self.assigned_to,
			"problem_description": self.description,
			"status": "Scheduled"
		})
		wo.insert(ignore_permissions=True)
		self.update_status("Assigned", f"Converted to Work Order {wo.name}")
		self.save(ignore_permissions=True)
		return wo.name

	def validate_employee(self):
		"""Validate that employee exists and get department"""
		if self.employee:
			emp = frappe.get_doc("Employee", self.employee)
			self.employee_name = emp.employee_name
			self.department = emp.department

	def validate_maintenance_type(self):
		"""Validate maintenance type and equipment category mapping"""
		if not self.equipment_category:
			frappe.throw(_("Equipment Category is mandatory"))

		allowed_types = CATEGORY_MAINTENANCE_TYPE_MAP.get(self.equipment_category, ["Non-IT"])

		if not self.maintenance_type:
			self.maintenance_type = allowed_types[0]
		elif self.maintenance_type not in allowed_types:
			frappe.throw(
				_("Maintenance Type '{0}' is invalid for Equipment Category '{1}'. Allowed Maintenance Type is '{2}'.").format(
					self.maintenance_type, self.equipment_category, ", ".join(allowed_types)
				)
			)

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
		if hasattr(self, "status") and self.status != new_status:
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
		if getattr(self, "status", None) and self.status not in ["Approved", "Assigned"]:
			frappe.throw(_("Request must be approved before assignment"))

		self.assigned_to = technician
		self.assigned_date = datetime.now()
		self.update_status("Assigned", f"Assigned to technician {technician}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} assigned to {1}").format(self.name, technician))

	def start_work(self):
		"""Technician starts work on the request"""
		if getattr(self, "status", None) and self.status != "Assigned":
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
		self.add_status_history(getattr(self, "status", "In Progress"), f"Diagnosis updated by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Diagnosis details saved for Maintenance Request {0}").format(self.name))

	def mark_resolved(self, resolution_notes="", root_cause=""):
		"""Technician marks the request as resolved"""
		if getattr(self, "status", None) and self.status != "In Progress":
			frappe.throw(_("Request must be in progress to mark as resolved"))

		self.resolution_date = datetime.now()
		self.resolution_notes = resolution_notes
		self.root_cause = root_cause
		self.update_status("Resolved", f"Marked as resolved by {frappe.session.user}")
		self.save()
		frappe.msgprint(_("Maintenance Request {0} marked as resolved").format(self.name))

	def verify_request(self, verification_status, feedback="", verified_by=None):
		"""Supervisor or Requester verifies the completed maintenance work"""
		if getattr(self, "status", None) and self.status != "Resolved":
			frappe.throw(_("Request must be resolved before verification"))

		self.verification_status = verification_status
		self.verification_feedback = feedback
		self.verification_date = datetime.now()
		self.verified_by = verified_by or frappe.session.user

		if verification_status == "Rework Required":
			self.update_status("In Progress", f"Rework requested during verification by {self.verified_by}")
		else:
			self.add_status_history(getattr(self, "status", "Verified"), f"Verified ({verification_status}) by {self.verified_by}")

		self.save()
		frappe.msgprint(_("Verification status updated for Maintenance Request {0}").format(self.name))

	def close_request(self, closing_remarks="", verified_by=""):
		"""Supervisor/Unit Head closes the request"""
		if getattr(self, "status", None) and self.status != "Resolved":
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
