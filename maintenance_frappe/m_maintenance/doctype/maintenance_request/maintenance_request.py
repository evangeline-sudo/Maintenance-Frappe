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

	def after_insert(self):
		"""After insert hook: log submitted status history, send submitted notification, and check approval rules"""
		self.add_status_history("Submitted", f"Request submitted for {self.ownership_type}")
		self.send_status_notification("Submitted")
		self.check_approval_requirement()

	def on_submit(self):
		"""On submit, add initial status history entry and check approval"""
		self.add_status_history("Submitted", f"Request submitted for {self.ownership_type}")
		self.send_status_notification("Submitted")
		self.check_approval_requirement()

	def send_status_notification(self, event_type):
		"""Send notification email using responsive Merriweather HTML Email Templates"""
		template_name_map = {
			"Submitted": "Maintenance Request Submitted",
			"Approval Required": "Maintenance Approval Required",
			"Approved": "Maintenance Request Approved",
			"Rejected": "Maintenance Request Rejected",
			"Assigned": "Maintenance Request Assigned",
			"Resolved": "Maintenance Work Resolved",
			"Rework Required": "Maintenance Rework Requested",
			"Closed": "Maintenance Request Closed",
		}
		template_name = template_name_map.get(event_type, "Maintenance Request Submitted")
		try:
			recipients = []
			if event_type == "Approval Required" and getattr(self, "unit_head", None) and "@" in str(self.unit_head):
				recipients.append(self.unit_head)
			if getattr(self, "assigned_to", None) and "@" in str(self.assigned_to):
				recipients.append(self.assigned_to)
			if getattr(self, "owner", None) and "@" in str(self.owner):
				recipients.append(self.owner)

			recipients = list(set(recipients))
			if not recipients:
				return

			if frappe.db.exists("Email Template", template_name):
				tmpl = frappe.get_doc("Email Template", template_name)
				subject = frappe.render_template(tmpl.subject, {"doc": self})
				message = frappe.render_template(tmpl.response, {"doc": self})
				frappe.sendmail(recipients=recipients, subject=subject, message=message)
			else:
				subject = f"Maintenance Request {self.name} - {event_type}"
				message = f"Maintenance Request {self.name} status updated to {self.status}."
				frappe.sendmail(recipients=recipients, subject=subject, message=message)
		except Exception as e:
			frappe.log_error(f"Failed to send email notification for {self.name}: {e}", "Notification Email Error")

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
		self.validate_issue_category_match()
		self.check_approved_status()
		self.calculate_total_costs()

	def auto_create_issue_category(self):
		"""Automatically create Issue Category if it does not exist"""
		if self.issue_category and not frappe.db.exists("Issue Category", self.issue_category):
			eq_cat = self.equipment_category if frappe.db.exists("Equipment Category", self.equipment_category) else None
			try:
				issue_cat = frappe.get_doc({
					"doctype": "Issue Category",
					"issue_category_name": self.issue_category,
					"equipment_category": eq_cat,
					"is_active": 1
				})
				issue_cat.insert(ignore_permissions=True)
			except Exception:
				pass

	def validate_issue_category_match(self):
		"""Server-side validation to ensure Issue Category belongs to the selected Equipment Category"""
		if self.issue_category and self.equipment_category:
			issue_cat_data = frappe.db.get_value(
				"Issue Category", self.issue_category, ["equipment_category", "is_active"], as_dict=True
			)
			if issue_cat_data:
				if not issue_cat_data.is_active:
					frappe.throw(_("Selected Issue Category '{0}' is inactive.").format(self.issue_category))
				if issue_cat_data.equipment_category and issue_cat_data.equipment_category != self.equipment_category:
					frappe.throw(
						_("Issue Category '{0}' does not belong to Equipment Category '{1}'.").format(
							self.issue_category, self.equipment_category
						)
					)

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
				self.equipment_category = eq_doc.equipment_category
			if getattr(eq_doc, "maintenance_type", None):
				self.maintenance_type = eq_doc.maintenance_type
			return

		# Check if equipment already exists in DB by serial or name
		existing_eq = None
		eq_serial = getattr(self, "equipment_serial", None)
		eq_name = getattr(self, "equipment_name", None)
		eq_category = getattr(self, "equipment_category", None)

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
				"maintenance_type": self.maintenance_type if self.maintenance_type in ["IT", "Non-IT", "Professional-Specialized"] else "Non-IT",
				"serial_number": self.equipment_serial,
				"department": getattr(self, "department", None),
				"unit": getattr(self, "unit", None),
				"status": "Active"
			})
			new_eq.insert(ignore_permissions=True)
			self.equipment = new_eq.name

	def fetch_employee_approver(self):
		"""Automatically resolve Unit Head / Approver from Employee record"""
		if not self.employee:
			return None
		emp = frappe.get_doc("Employee", self.employee)
		# 1. Check reports_to employee user
		if emp.reports_to:
			approver_user = frappe.db.get_value("Employee", emp.reports_to, "user_id")
			if approver_user:
				return approver_user
		# 2. Check department head
		if emp.department:
			dept_head = frappe.db.get_value("Department", emp.department, "custom_department_head") or frappe.db.get_value("Department", emp.department, "disabled")
			if dept_head:
				return dept_head
		return None

	def check_approved_status(self):
		"""Ensure status is set to Approved when approval_status is Approved"""
		if hasattr(self, "status") and self.approval_status == "Approved" and self.status in ["Submitted", "Pending Approval"]:
			self.status = "Approved"

	def validate_employee(self):
		"""Validate that employee exists and get department and unit"""
		if self.employee:
			emp = frappe.get_doc("Employee", self.employee)
			self.employee_name = emp.employee_name
			if getattr(emp, "department", None):
				self.department = emp.department
			if getattr(emp, "unit", None):
				self.unit = emp.unit
			if not getattr(self, "unit_head", None):
				self.unit_head = self.fetch_employee_approver()

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
		"""Determine if Unit Head approval is required based on rules"""
		rule = frappe.db.get_value(
			"Maintenance Approval Rule",
			{
				"unit": getattr(self, "unit", "") or "",
				"department": getattr(self, "department", "") or "",
				"category": getattr(self, "category", "") or "",
				"priority": getattr(self, "priority", "Medium"),
				"disabled": 0
			},
			["name", "requires_approval", "approval_authority"],
			as_dict=True
		)

		requires_approval = rule.requires_approval if rule else False

		if requires_approval:
			self.update_status("Pending Approval", "Awaiting Unit Head approval")
			self.approval_status = "Pending"
			if not self.unit_head:
				self.unit_head = self.fetch_employee_approver()
			if self.unit_head:
				self.create_approval_todo()
			self.send_status_notification("Approval Required")
		else:
			self.update_status("Approved", "Auto-approved")
			self.approval_status = "Approved"
			self.approval_date = datetime.now()
			self.send_status_notification("Approved")

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
		if self.unit_head:
			todo = frappe.get_doc({
				"doctype": "ToDo",
				"owner": self.unit_head,
				"description": f"Approval required for Maintenance Request {self.name}",
				"reference_type": "Maintenance Request",
				"reference_name": self.name,
				"priority": "High" if self.priority == "Critical" else "Medium"
			})
			todo.insert(ignore_permissions=True)

	@frappe.whitelist()
	def approve_request(self, remarks=""):
		"""Unit Head approves the maintenance request"""
		if self.approval_status != "Pending" and self.status != "Pending Approval":
			frappe.throw(_("Only pending requests can be approved"))

		self.approval_status = "Approved"
		self.approval_date = datetime.now()
		self.approval_notes = remarks
		self.update_status("Approved", f"Approved by {frappe.session.user}: {remarks}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Approved")
		frappe.msgprint(_("Maintenance Request {0} approved").format(self.name))

	@frappe.whitelist()
	def reject_request(self, remarks=""):
		"""Unit Head rejects the maintenance request"""
		if self.approval_status != "Pending" and self.status != "Pending Approval":
			frappe.throw(_("Only pending requests can be rejected"))

		self.approval_status = "Rejected"
		self.approval_notes = remarks
		self.closed_date = datetime.now()
		self.update_status("Rejected", f"Rejected by {frappe.session.user}: {remarks}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Rejected")
		frappe.msgprint(_("Maintenance Request {0} rejected and closed.").format(self.name))

	@frappe.whitelist()
	def assign_technician(self, team=None, technician=None, expected_date=None, remarks=""):
		"""Admin/Supervisor assigns maintenance team and technician"""
		if team:
			self.assigned_team = team
		if technician:
			self.assigned_to = technician
		if expected_date:
			self.estimated_completion_time = expected_date

		self.assigned_date = datetime.now()
		self.update_status("Assigned", f"Assigned to {technician or team} by {frappe.session.user}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Assigned")
		frappe.msgprint(_("Maintenance Request {0} assigned").format(self.name))

	@frappe.whitelist()
	def start_maintenance_work(self):
		"""Technician starts maintenance work"""
		self.update_status("In Progress", f"Work started by {frappe.session.user}")
		self.save(ignore_permissions=True)
		frappe.msgprint(_("Work started on Maintenance Request {0}").format(self.name))

	@frappe.whitelist()
	def put_on_hold(self, reason="Parts Unavailable / Vendor Delay"):
		"""Put maintenance work on hold (returns to Planning state)"""
		self.update_status("On Hold", f"Put on hold by {frappe.session.user}: {reason}")
		self.save(ignore_permissions=True)
		frappe.msgprint(_("Maintenance Request {0} put on hold ({1})").format(self.name, reason))

	@frappe.whitelist()
	def resume_work(self):
		"""Resume maintenance work from hold"""
		self.update_status("In Progress", f"Work resumed by {frappe.session.user}")
		self.save(ignore_permissions=True)
		frappe.msgprint(_("Work resumed on Maintenance Request {0}").format(self.name))

	@frappe.whitelist()
	def resolve_maintenance(self, resolution_type=None, resolution_details="", diagnosis="", work_details="", failure_cause=None):
		"""Technician marks maintenance work as resolved"""
		if resolution_type:
			self.resolution_type = resolution_type
		if resolution_details:
			self.resolution_notes = resolution_details
		if diagnosis:
			self.diagnosis_notes = diagnosis
		if work_details:
			self.work_performed = work_details
		if failure_cause:
			self.root_cause = failure_cause

		self.resolution_date = datetime.now()
		self.update_status("Resolved", f"Marked resolved by {frappe.session.user}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Resolved")
		frappe.msgprint(_("Maintenance Request {0} resolved").format(self.name))

	@frappe.whitelist()
	def verify_and_close(self, remarks=""):
		"""Supervisor/Admin verifies completed work and closes request"""
		self.verification_status = "Verified"
		self.verification_feedback = remarks
		self.verification_date = datetime.now()
		self.verified_by = frappe.session.user
		self.closed_date = datetime.now()
		self.closing_remarks = remarks
		self.update_status("Closed", f"Verified and closed by {frappe.session.user}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Closed")
		frappe.msgprint(_("Maintenance Request {0} verified and closed").format(self.name))

	@frappe.whitelist()
	def request_rework(self, remarks=""):
		"""Supervisor requests rework if inspection/verification fails"""
		self.verification_status = "Rework Required"
		self.verification_feedback = remarks
		self.verification_date = datetime.now()
		self.verified_by = frappe.session.user
		self.update_status("In Progress", f"Rework requested by {frappe.session.user}: {remarks}")
		self.save(ignore_permissions=True)
		self.send_status_notification("Rework Required")
		frappe.msgprint(_("Rework requested for Maintenance Request {0}").format(self.name))

	@frappe.whitelist()
	def create_work_order(self):
		"""Create linked Work Order for request"""
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

	def send_status_notification(self, event_type):
		"""Send notification email using Email Template to employee, approver, or technician"""
		try:
			template_name = f"Maintenance Request {event_type}"
			if event_type == "Approval Required":
				template_name = "Maintenance Approval Required"
			elif event_type == "Resolved" or event_type == "Work Resolved":
				template_name = "Maintenance Work Resolved"
			elif event_type == "Rework Required" or event_type == "Rework Requested":
				template_name = "Maintenance Rework Requested"

			recipients = set()
			if self.owner and "@" in self.owner:
				recipients.add(self.owner)
			if getattr(self, "employee_email", None) and "@" in self.employee_email:
				recipients.add(self.employee_email)
			if getattr(self, "unit_head", None) and "@" in self.unit_head:
				recipients.add(self.unit_head)
			if self.assigned_to and "@" in self.assigned_to:
				recipients.add(self.assigned_to)

			if not recipients:
				return

			recipients_list = list(recipients)

			if frappe.db.exists("Email Template", template_name):
				template = frappe.get_doc("Email Template", template_name)
				subject = frappe.render_template(template.subject, {"doc": self})
				html_content = template.response_html or template.response
				message = frappe.render_template(html_content, {"doc": self})
			else:
				subject = f"Maintenance Request {self.name} - {event_type}"
				message = f"Maintenance Request {self.name} status updated to {self.status}.<br>Equipment: {self.equipment_name or self.equipment_category}<br>Description: {self.description}"

			frappe.sendmail(recipients=recipients_list, subject=subject, message=message)
		except Exception as e:
			frappe.log_error(f"Error sending email notification for {self.name}: {str(e)}", "Maintenance Request Email Notification")

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
		self.save(ignore_permissions=True)

	def add_parts_used(self, item, quantity, uom="", rate=0, notes=""):
		"""Add parts used entry and update stock"""
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
		self.save(ignore_permissions=True)

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

