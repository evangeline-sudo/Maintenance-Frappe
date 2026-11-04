# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, getdate, now_datetime, today


class PreventiveMaintenancePlan(Document):
	def validate(self):
		if not self.start_date:
			self.start_date = today()
		if not self.next_due_date:
			self.next_due_date = self.start_date

		if self.equipment and frappe.db.exists("Equipment", self.equipment):
			eq = frappe.db.get_value(
				"Equipment",
				self.equipment,
				["equipment_name", "equipment_category", "department", "maintenance_team", "responsible_person"],
				as_dict=True
			)
			if eq:
				if not self.equipment_name:
					self.equipment_name = eq.equipment_name
				if not self.equipment_category:
					self.equipment_category = eq.equipment_category
				if not getattr(self, "department", None) and eq.get("department"):
					self.department = eq.department
				if not self.assigned_team and eq.get("maintenance_team"):
					self.assigned_team = eq.maintenance_team

	def calculate_next_due_date(self, base_date=None):
		"""Calculate the next due date based on the plan's frequency."""
		base = getdate(base_date or self.next_due_date or today())
		freq = self.frequency or "Monthly"

		if freq == "Daily":
			return add_days(base, 1)
		elif freq == "Weekly":
			return add_days(base, 7)
		elif freq == "Monthly":
			return add_months(base, 1)
		elif freq == "Quarterly":
			return add_months(base, 3)
		elif freq == "Half-Yearly":
			return add_months(base, 6)
		elif freq == "Yearly":
			return add_years(base, 1)
		elif freq == "Custom Days":
			interval = int(self.custom_interval_days or 30)
			return add_days(base, interval)
		else:
			return add_months(base, 1)

	@frappe.whitelist()
	def generate_work_order(self):
		"""Generate a scheduled Work Order for this preventive maintenance plan."""
		if not self.equipment:
			frappe.throw(_("Equipment is required to generate a Work Order."))

		eq_location = None
		eq_dept = None
		if frappe.db.exists("Equipment", self.equipment):
			eq_info = frappe.db.get_value("Equipment", self.equipment, ["used_in_location", "department"], as_dict=True)
			if eq_info:
				eq_location = eq_info.get("used_in_location")
				eq_dept = eq_info.get("department")

		wo = frappe.get_doc({
			"doctype": "Work Order",
			"pm_plan": self.name,
			"equipment": self.equipment,
			"equipment_name": self.equipment_name,
			"location": eq_location,
			"department": eq_dept,
			"maintenance_type": self.maintenance_type or "Preventive",
			"priority": 3,
			"assigned_team": self.assigned_team,
			"assigned_technician": self.assigned_technician,
			"planned_start": now_datetime(),
			"problem_description": f"Scheduled Preventive Maintenance: {self.plan_name}\n\n{self.instructions or 'Perform standard preventive maintenance and inspection routine.'}",
			"status": "Scheduled"
		})
		wo.flags.ignore_mandatory = True
		wo.insert(ignore_permissions=True)

		self.last_generated_date = today()
		self.next_due_date = self.calculate_next_due_date(self.next_due_date)
		self.save(ignore_permissions=True)

		return wo.name


@frappe.whitelist()
def process_due_plans():
	"""Process due preventive maintenance plans and generate scheduled work orders."""
	current_today = getdate(today())
	due_plans = frappe.get_all(
		"Preventive Maintenance Plan",
		filters={
			"status": "Active",
			"next_due_date": ["<=", current_today]
		},
		pluck="name"
	)

	generated = []
	for plan_name in due_plans:
		try:
			plan_doc = frappe.get_doc("Preventive Maintenance Plan", plan_name)
			wo_name = plan_doc.generate_work_order()
			if wo_name:
				generated.append({"plan": plan_name, "work_order": wo_name})
		except Exception as e:
			frappe.log_error(f"Failed to generate Work Order for PM Plan {plan_name}: {e}")

	return generated
