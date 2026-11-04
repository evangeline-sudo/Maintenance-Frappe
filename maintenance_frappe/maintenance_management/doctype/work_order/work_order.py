# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime


class WorkOrder(Document):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.flags.ignore_mandatory = True

	def _load_child_table_from_db(self, fieldname, child_doctype):
		"""Safely handle child table loading to prevent unknown column 'parent' crashes"""
		if child_doctype == "Maintenance Tool":
			child_doctype = "Work Order Tool"
			if not hasattr(frappe, "db") or not frappe.db.table_exists("Work Order Tool"):
				return []
		try:
			return super()._load_child_table_from_db(fieldname, child_doctype)
		except Exception:
			return []

	def before_insert(self):
		self.flags.ignore_mandatory = True

	def before_validate(self):
		self.flags.ignore_mandatory = True

	def validate(self):
		self.flags.ignore_mandatory = True
		self.calculate_total_cost()
		self.sync_maintenance_request_details()
		self.validate_equipment()

	def calculate_total_cost(self):
		"""Calculate total cost from labor, parts, tools, and vendor costs"""
		labor = float(getattr(self, "labor_cost", 0.0) or 0.0)
		parts = float(getattr(self, "parts_cost", 0.0) or 0.0)
		tools = float(getattr(self, "tool_cost", 0.0) or 0.0)
		vendor = float(getattr(self, "vendor_cost", 0.0) or 0.0)
		self.total_cost = labor + parts + tools + vendor

	def sync_maintenance_request_details(self):
		"""Auto-fetch unit and department details from linked Maintenance Request"""
		if getattr(self, "maintenance_request", None) and frappe.db.exists("Maintenance Request", self.maintenance_request):
			fields_to_fetch = ["department", "equipment"]
			meta = frappe.get_meta("Maintenance Request")
			if meta.has_field("custom_unit"):
				fields_to_fetch.append("custom_unit")
			if meta.has_field("maintenance_type"):
				fields_to_fetch.append("maintenance_type")
			if meta.has_field("priority"):
				fields_to_fetch.append("priority")
			if meta.has_field("description"):
				fields_to_fetch.append("description")

			mr = frappe.db.get_value(
				"Maintenance Request",
				self.maintenance_request,
				fields_to_fetch,
				as_dict=True,
			)
			if mr:
				if hasattr(self, "custom_unit") and mr.get("custom_unit"):
					self.custom_unit = mr.custom_unit
				if not getattr(self, "department", None) and mr.get("department"):
					self.department = mr.department
				if not getattr(self, "equipment", None) and mr.get("equipment"):
					self.equipment = mr.equipment
				if not getattr(self, "maintenance_type", None) and mr.get("maintenance_type"):
					valid_wo_types = [
						"Corrective", "Preventive", "Predictive", "Emergency",
						"Routine", "Breakdown", "Inspection", "Calibration", "Servicing"
					]
					if mr.maintenance_type in valid_wo_types:
						self.maintenance_type = mr.maintenance_type
					else:
						self.maintenance_type = "Corrective"
				if not getattr(self, "priority", None) and mr.get("priority"):
					self.priority = mr.priority
				if not getattr(self, "problem_description", None) and mr.get("description"):
					self.problem_description = mr.description

	def validate_equipment(self):
		"""Auto-fetch equipment details if available"""
		if getattr(self, "equipment", None) and frappe.db.exists("Equipment", self.equipment):
			eq = frappe.db.get_value(
				"Equipment",
				self.equipment,
				["equipment_name", "used_in_location", "department"],
				as_dict=True,
			)
			if eq:
				if not getattr(self, "equipment_name", None) and eq.get("equipment_name"):
					self.equipment_name = eq.equipment_name
				if not getattr(self, "location", None) and eq.get("used_in_location"):
					self.location = eq.used_in_location
				if not getattr(self, "department", None) and eq.get("department"):
					self.department = eq.department
