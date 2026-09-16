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

EQUIPMENT_CATEGORY_ALIASES = {
	"IT Equipment": ["IT Equipment", "IT", "Network", "Hardware", "Computer", "Laptop", "Server"],
	"Electrical Equipment": ["Electrical Equipment", "Electrical", "Power", "Generator", "UPS", "Transformer"],
	"Vehicle": ["Vehicle", "Vehicles", "Automobile", "Fleet", "Car", "Truck", "Van"],
	"Machine": ["Machine", "Machinery", "Mechanical Equipment", "Plant Machinery", "Apparatus"],
	"Furniture": ["Furniture", "Fixtures", "Furniture & Fixtures"],
	"Building/Facility": ["Building/Facility", "Building", "Facility", "HVAC", "Civil", "Infrastructure"],
	"Medical Equipment": ["Medical Equipment", "Medical", "Biomedical", "Clinical", "Healthcare"],
	"Office Equipment": ["Office Equipment", "Office", "Printer", "Copier", "Scanner"],
	"Other": ["Other", "General", "Miscellaneous"]
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
		self.validate_approval_status_permissions()
		self.validate_equipment_category_match()
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
		"""Validate that employee exists, set employee_name, and auto-populate unit_head if missing"""
		if self.employee:
			emp = frappe.get_doc("Employee", self.employee)
			self.employee_name = emp.employee_name
			if hasattr(self, "department") and getattr(emp, "department", None):
				self.department = emp.department

			# Auto-populate unit_head (User) from employee details if not already set
			if not self.unit_head:
				manager_info = get_employee_manager_user(self.employee)
				if manager_info and manager_info.get("user_id"):
					self.unit_head = manager_info["user_id"]

	def validate_approval_status_permissions(self):
		"""
		Enforce that Approval Status can only be changed by:
		- Maintenance Manager
		- System Manager
		- Administrator
		- Assigned Unit Head / Manager User (self.unit_head)
		"""
		current_user = frappe.session.user
		if current_user == "Administrator":
			return

		user_roles = frappe.get_roles(current_user)
		is_manager = any(role in user_roles for role in ["Administrator", "System Manager", "Maintenance Manager"])
		is_unit_head = bool(self.unit_head and current_user == self.unit_head)

		# If creating a new document
		if self.is_new():
			# Regular users can only submit with approval_status = 'Pending'
			if self.approval_status and self.approval_status != "Pending":
				if not (is_manager or is_unit_head):
					frappe.throw(
						_("Only Maintenance Manager or the assigned Unit Head ({0}) can set Approval Status to '{1}'.").format(
							self.unit_head or _("Unit Head"), self.approval_status
						)
					)
			return

		# If updating an existing document and approval_status changed
		if self.has_value_changed("approval_status"):
			if not (is_manager or is_unit_head):
				frappe.throw(
					_("Only Maintenance Manager or the assigned Unit Head/Manager ({0}) can change the Approval Status.").format(
						self.unit_head or _("Unit Head")
					)
				)

			# Record approval/rejection timestamp and audit history
			if self.approval_status == "Approved":
				self.approval_date = datetime.now()
				self.add_status_history("Approved", f"Approved by {current_user}")
			elif self.approval_status == "Rejected":
				self.approval_date = datetime.now()
				self.add_status_history("Rejected", f"Rejected by {current_user}")
			elif self.approval_status == "Hold":
				self.add_status_history("Hold", f"Placed on Hold by {current_user}")

	def validate_approval_authority(self):
		"""Validate that current user has authority to approve/reject"""
		current_user = frappe.session.user
		if current_user == "Administrator":
			return True

		user_roles = frappe.get_roles(current_user)
		is_authorized = (
			any(role in user_roles for role in ["System Manager", "Maintenance Manager"]) or
			bool(self.unit_head and current_user == self.unit_head)
		)
		if not is_authorized:
			frappe.throw(
				_("Only Maintenance Manager or the assigned Unit Head/Manager ({0}) can approve or reject this request.").format(
					self.unit_head or _("Unit Head")
				)
			)
		return True

	def validate_equipment_category_match(self):
		"""Ensure equipment matches equipment_category if both are selected"""
		if self.equipment and self.equipment_category:
			eq_cat = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
			if eq_cat:
				matching_cats = get_matching_equipment_categories(self.equipment_category)
				if eq_cat not in matching_cats:
					category_map = {
						"Electrical": "Electrical Equipment",
						"IT": "IT Equipment",
						"Vehicles": "Vehicle",
						"Medical": "Medical Equipment",
						"HVAC": "Building/Facility",
						"Network": "IT Equipment"
					}
					mapped = category_map.get(eq_cat, eq_cat)
					if mapped != self.equipment_category and eq_cat not in matching_cats:
						frappe.throw(
							_("Selected Equipment '{0}' belongs to category '{1}', which does not match the request category '{2}'.").format(
								self.equipment, eq_cat, self.equipment_category
							)
						)

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
		"""Maintenance Manager or Unit Head approves the maintenance request"""
		self.validate_approval_authority()
		if self.approval_status not in ["Pending", "Hold"]:
			frappe.throw(_("Only pending or on-hold requests can be approved"))

		self.approval_status = "Approved"
		self.approval_date = datetime.now()
		if approval_notes:
			self.approval_notes = approval_notes
		self.update_status("Approved", f"Approved by {frappe.session.user}")
		self.save(ignore_permissions=True)
		frappe.msgprint(_("Maintenance Request {0} approved").format(self.name))

	def reject_request(self, approval_notes=""):
		"""Maintenance Manager or Unit Head rejects the maintenance request"""
		self.validate_approval_authority()
		if self.approval_status not in ["Pending", "Hold"]:
			frappe.throw(_("Only pending or on-hold requests can be rejected"))

		self.approval_status = "Rejected"
		self.approval_date = datetime.now()
		if approval_notes:
			self.approval_notes = approval_notes
		self.update_status("Rejected", f"Rejected by {frappe.session.user}")
		self.save(ignore_permissions=True)
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


def find_manager_by_role(emp):
	"""
	Search for a manager/unit head Employee based on the 'role' field in Employee DocType:
	1. Check within the same unit / custom_unit or department.
	2. If not found in same unit/dept, check across all active Employees.
	3. Check by Frappe Has Role ('Unit Head', 'Maintenance Manager').
	"""
	emp_name = getattr(emp, "name", "")
	emp_unit = getattr(emp, "custom_unit", getattr(emp, "unit", None))
	emp_dept = getattr(emp, "department", None)

	# 1. First priority: look in the same unit / department for an Employee with manager/unit head role
	query_same_unit = """
		SELECT name, employee_name, user_id, role
		FROM `tabEmployee`
		WHERE status = 'Active'
		  AND name != %(emp_name)s
		  AND (
			role IN ('Unit Head', 'Maintenance Manager', 'Manager', 'Department Head', 'Supervisor')
			OR role LIKE '%%Unit Head%%'
			OR role LIKE '%%Manager%%'
			OR custom_role IN ('Unit Head', 'Maintenance Manager', 'Manager', 'Department Head', 'Supervisor')
			OR custom_role LIKE '%%Unit Head%%'
			OR custom_role LIKE '%%Manager%%'
			OR designation LIKE '%%Unit Head%%'
			OR designation LIKE '%%Manager%%'
			OR is_manager = 1
			OR custom_is_manager = 1
			OR is_unit_head = 1
			OR custom_is_unit_head = 1
		  )
		  AND (
			(%(emp_unit)s IS NOT NULL AND (custom_unit = %(emp_unit)s OR unit = %(emp_unit)s))
			OR (%(emp_dept)s IS NOT NULL AND department = %(emp_dept)s)
		  )
		ORDER BY 
			CASE 
				WHEN role = 'Unit Head' OR custom_role = 'Unit Head' THEN 1
				WHEN role LIKE '%%Unit Head%%' OR custom_role LIKE '%%Unit Head%%' THEN 2
				WHEN role = 'Maintenance Manager' OR custom_role = 'Maintenance Manager' THEN 3
				WHEN is_manager = 1 OR custom_is_manager = 1 THEN 4
				ELSE 5 
			END ASC
		LIMIT 1
	"""
	try:
		mgr = frappe.db.sql(query_same_unit, {"emp_name": emp_name, "emp_unit": emp_unit, "emp_dept": emp_dept}, as_dict=True)
		if mgr and mgr[0].get("user_id"):
			return mgr[0]
	except Exception:
		pass

	# 2. Second priority: look globally for an Employee with Unit Head or Maintenance Manager role
	query_global = """
		SELECT name, employee_name, user_id, role
		FROM `tabEmployee`
		WHERE status = 'Active'
		  AND name != %(emp_name)s
		  AND (
			role IN ('Unit Head', 'Maintenance Manager')
			OR role LIKE '%%Unit Head%%'
			OR custom_role IN ('Unit Head', 'Maintenance Manager')
			OR custom_role LIKE '%%Unit Head%%'
			OR is_manager = 1
			OR custom_is_manager = 1
			OR is_unit_head = 1
		  )
		ORDER BY 
			CASE 
				WHEN role = 'Unit Head' OR custom_role = 'Unit Head' THEN 1
				WHEN is_unit_head = 1 THEN 2
				ELSE 3 
			END ASC
		LIMIT 1
	"""
	try:
		mgr = frappe.db.sql(query_global, {"emp_name": emp_name}, as_dict=True)
		if mgr and mgr[0].get("user_id"):
			return mgr[0]
	except Exception:
		pass

	# 3. Third priority: look by Frappe User Role in tabHas Role
	try:
		users_with_role = frappe.db.sql("""
			SELECT DISTINCT e.name, e.employee_name, e.user_id
			FROM `tabEmployee` e
			JOIN `tabHas Role` hr ON hr.parent = e.user_id
			WHERE e.status = 'Active'
			  AND e.name != %(emp_name)s
			  AND hr.role IN ('Unit Head', 'Maintenance Manager')
			ORDER BY CASE WHEN hr.role = 'Unit Head' THEN 1 ELSE 2 END ASC
			LIMIT 1
		""", {"emp_name": emp_name}, as_dict=True)
		if users_with_role and users_with_role[0].get("user_id"):
			return users_with_role[0]
	except Exception:
		pass

	return None


@frappe.whitelist()
def get_employee_manager_user(employee=None):
	"""
	Determine the Manager / Unit Head (User) based on Employee details and Role:
	1. If the selected employee has 'is_manager' enabled or their Role is 'Unit Head' / 'Manager':
	   The employee themselves is the manager/unit head; return their linked user_id.
	2. If not, check if the employee's 'reports_to' has a linked user_id.
	3. Find the manager/unit head from the Employee 'role' field (in the same unit/department or globally).
	4. Fallback to Department Head in Department DocType.
	"""
	if not employee:
		return {}

	emp = frappe.get_doc("Employee", employee)
	emp_role = getattr(emp, "role", getattr(emp, "custom_role", getattr(emp, "designation", ""))) or ""
	emp_role_str = str(emp_role).lower()

	result = {
		"employee_name": emp.employee_name,
		"employee_role": emp_role,
		"department": getattr(emp, "department", None),
		"unit": getattr(emp, "custom_unit", getattr(emp, "unit", None)),
		"user_id": None
	}

	# Check 1: Is this employee themselves a Manager or Unit Head?
	# Enabled via is_manager / custom_is_manager / is_unit_head OR via role field
	is_manager_flag = bool(
		getattr(emp, "is_manager", 0) or 
		getattr(emp, "custom_is_manager", 0) or 
		getattr(emp, "is_unit_head", 0) or 
		getattr(emp, "custom_is_unit_head", 0)
	)
	is_manager_role = (
		"unit head" in emp_role_str or 
		"manager" in emp_role_str or 
		"supervisor" in emp_role_str or
		"head" in emp_role_str
	)

	if (is_manager_flag or is_manager_role) and getattr(emp, "user_id", None):
		result["user_id"] = emp.user_id
		result["manager_employee"] = emp.name
		result["manager_name"] = emp.employee_name
		result["source"] = "self_is_manager_or_role"
		return result

	# Check 2: Reports To (Direct Supervisor / Manager Employee)
	reports_to = getattr(emp, "reports_to", None)
	if reports_to:
		mgr_doc = frappe.db.get_value("Employee", reports_to, ["user_id", "employee_name"], as_dict=True)
		if mgr_doc and mgr_doc.get("user_id"):
			result["user_id"] = mgr_doc["user_id"]
			result["manager_employee"] = reports_to
			result["manager_name"] = mgr_doc.get("employee_name")
			result["source"] = "reports_to"
			return result

	# Check 3: Find Manager / Unit Head from Employee Role fields
	mgr_by_role = find_manager_by_role(emp)
	if mgr_by_role and mgr_by_role.get("user_id"):
		result["user_id"] = mgr_by_role["user_id"]
		result["manager_employee"] = mgr_by_role.get("name")
		result["manager_name"] = mgr_by_role.get("employee_name")
		result["source"] = "employee_role"
		return result

	# Check 4: Check Department Head from Department DocType
	dept = getattr(emp, "department", None)
	if dept and frappe.db.exists("Department", dept):
		dept_doc = frappe.get_doc("Department", dept)
		dept_head = getattr(dept_doc, "department_head", None)
		if dept_head:
			dept_head_user = frappe.db.get_value("Employee", dept_head, "user_id") or dept_head
			if frappe.db.exists("User", dept_head_user):
				result["user_id"] = dept_head_user
				result["manager_employee"] = dept_head
				result["source"] = "department_head"
				return result

	# Check 5: Check if employee has user_id
	if getattr(emp, "user_id", None):
		result["employee_user_id"] = emp.user_id

	return result


@frappe.whitelist()
def get_matching_equipment_categories(equipment_category=None):
	"""Return a list of category names matching the given equipment_category or its aliases"""
	if not equipment_category:
		return []

	aliases = EQUIPMENT_CATEGORY_ALIASES.get(equipment_category, [equipment_category])
	matched = set(aliases)
	keywords = [equipment_category.lower()]
	for a in aliases:
		keywords.append(a.lower())

	if frappe.db.table_exists("Equipment Category"):
		try:
			existing_cats = frappe.db.get_all("Equipment Category", fields=["name", "category_name"])
			for cat in existing_cats:
				c_name = cat.get("category_name") or cat.get("name")
				if c_name:
					c_lower = c_name.lower()
					if any(k in c_lower or c_lower in k for k in keywords):
						matched.add(cat.get("name"))
						if cat.get("category_name"):
							matched.add(cat.get("category_name"))
		except Exception:
			pass

	return list(matched)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_equipment_for_category(doctype, txt, searchfield, start, page_len, filters):
	"""
	Filter equipment by equipment_category and active status for Link field queries.
	"""
	equipment_category = filters.get("equipment_category") if filters else None
	conditions = ["status NOT IN ('Retired', 'Disposed')"]
	params = {}

	if equipment_category:
		matching_cats = get_matching_equipment_categories(equipment_category)
		if matching_cats:
			placeholders = ", ".join([f"%({f'cat_{i}'})s" for i in range(len(matching_cats))])
			conditions.append(f"equipment_category IN ({placeholders})")
			for i, cat in enumerate(matching_cats):
				params[f"cat_{i}"] = cat
		else:
			conditions.append("equipment_category = %(equipment_category)s")
			params["equipment_category"] = equipment_category

	if txt:
		conditions.append("(name LIKE %(txt)s OR equipment_name LIKE %(txt)s OR serial_number LIKE %(txt)s)")
		params["txt"] = f"%{txt}%"

	where_clause = " AND ".join(conditions)
	query = f"""
		SELECT name, equipment_name, serial_number, location, equipment_category
		FROM `tabEquipment`
		WHERE {where_clause}
		ORDER BY name ASC
		LIMIT %(start)s, %(page_len)s
	"""
	params["start"] = int(start or 0)
	params["page_len"] = int(page_len or 20)

	return frappe.db.sql(query, params)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_manager_users(doctype, txt, searchfield, start, page_len, filters):
	"""
	Return users who are:
	- Linked to an Employee with is_manager / custom_is_manager = 1
	- Or linked to an Employee who has reports_to pointing to them
	- Or have role Unit Head, Maintenance Manager, System Manager, Administrator
	"""
	manager_roles = ("System Manager", "Administrator", "Maintenance Manager", "Unit Head", "Supervisor")
	role_users = frappe.db.get_all(
		"Has Role",
		filters={"role": ["in", manager_roles]},
		pluck="parent"
	)

	emp_users = []
	try:
		emp_users = frappe.db.sql_list("""
			SELECT DISTINCT user_id FROM `tabEmployee`
			WHERE user_id IS NOT NULL AND user_id != ''
			AND (
				role IN ('Unit Head', 'Maintenance Manager', 'Manager', 'Department Head', 'Supervisor')
				OR role LIKE '%%Unit Head%%'
				OR role LIKE '%%Manager%%'
				OR custom_role IN ('Unit Head', 'Maintenance Manager', 'Manager', 'Department Head', 'Supervisor')
				OR custom_role LIKE '%%Unit Head%%'
				OR custom_role LIKE '%%Manager%%'
				OR designation LIKE '%%Unit Head%%'
				OR designation LIKE '%%Manager%%'
				OR is_manager = 1 OR custom_is_manager = 1
				OR is_unit_head = 1 OR custom_is_unit_head = 1
				OR name IN (SELECT DISTINCT reports_to FROM `tabEmployee` WHERE reports_to IS NOT NULL AND reports_to != '')
			)
		""")
	except Exception:
		try:
			emp_users = frappe.db.sql_list("""
				SELECT DISTINCT user_id FROM `tabEmployee`
				WHERE user_id IS NOT NULL AND user_id != ''
				AND (
					is_manager = 1 OR custom_is_manager = 1
					OR name IN (SELECT DISTINCT reports_to FROM `tabEmployee` WHERE reports_to IS NOT NULL AND reports_to != '')
				)
			""")
		except Exception:
			pass

	eligible_users = list(set(role_users + emp_users))
	params = {
		"txt": f"%{txt}%",
		"start": int(start or 0),
		"page_len": int(page_len or 20)
	}

	if not eligible_users:
		return frappe.db.sql("""
			SELECT name, full_name, email FROM `tabUser`
			WHERE enabled = 1 AND (name LIKE %(txt)s OR full_name LIKE %(txt)s OR email LIKE %(txt)s)
			ORDER BY name ASC LIMIT %(start)s, %(page_len)s
		""", params)

	placeholders = ", ".join([f"%({f'u_{i}'})s" for i in range(len(eligible_users))])
	for i, u in enumerate(eligible_users):
		params[f"u_{i}"] = u

	return frappe.db.sql(f"""
		SELECT name, full_name, email FROM `tabUser`
		WHERE enabled = 1 AND name IN ({placeholders})
		AND (name LIKE %(txt)s OR full_name LIKE %(txt)s OR email LIKE %(txt)s)
		ORDER BY name ASC LIMIT %(start)s, %(page_len)s
	""", params)
