import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, getdate

class PreventiveMaintenancePlan(Document):
	def validate(self):
		if not self.next_due_date and self.start_date:
			self.next_due_date = self.start_date

	def calculate_next_due_date(self, current_date=None):
		base_date = getdate(current_date or self.next_due_date or self.start_date)
		freq = self.frequency
		if freq == "Daily":
			return add_days(base_date, 1)
		elif freq == "Weekly":
			return add_days(base_date, 7)
		elif freq == "Monthly":
			return add_months(base_date, 1)
		elif freq == "Quarterly":
			return add_months(base_date, 3)
		elif freq == "Half-Yearly":
			return add_months(base_date, 6)
		elif freq == "Yearly":
			return add_years(base_date, 1)
		elif freq == "Custom Days" and self.custom_interval_days:
			return add_days(base_date, int(self.custom_interval_days))
		return add_months(base_date, 1)

	def generate_work_order(self):
		if self.status != "Active":
			return None

		wo = frappe.get_doc({
			"doctype": "Work Order",
			"equipment": self.equipment,
			"equipment_name": self.equipment_name,
			"maintenance_type": self.maintenance_type,
			"priority": "Medium",
			"assigned_team": self.assigned_team,
			"assigned_technician": self.assigned_technician,
			"planned_start": self.next_due_date,
			"problem_description": f"Scheduled Preventive Maintenance Plan: {self.plan_name}",
			"pm_plan": self.name,
			"status": "Scheduled"
		})
		
		# Copy checklist items if template provided
		if self.checklist and frappe.db.exists("Maintenance Checklist", self.checklist):
			tmpl = frappe.get_doc("Maintenance Checklist", self.checklist)
			for item in tmpl.items:
				wo.append("checklist_items", {
					"inspection_item": item.inspection_item,
					"expected_result": item.expected_result,
					"status": "Pass"
				})

		wo.insert(ignore_permissions=True)
		self.last_generated_date = getdate()
		self.next_due_date = self.calculate_next_due_date(self.next_due_date)
		self.save(ignore_permissions=True)
		return wo.name


def process_due_plans():
	today = getdate()
	due_plans = frappe.get_all(
		"Preventive Maintenance Plan",
		filters={"status": "Active", "next_due_date": ["<=", today]},
		pluck="name"
	)
	for plan_name in due_plans:
		try:
			plan_doc = frappe.get_doc("Preventive Maintenance Plan", plan_name)
			plan_doc.generate_work_order()
		except Exception as e:
			frappe.log_error(f"Error processing PM Plan {plan_name}: {e}", "PM Scheduler Error")

