# Copyright (c) 2026, Evangeline  and Contributors
# See license.txt

# import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



import unittest
import frappe

class IntegrationTestMaintenanceRequest(unittest.TestCase):
	"""
	Integration tests for MaintenanceRequest.
	Tests automatic issue category creation, equipment auto-creation/linking,
	approval status updates, and Work Order generation.
	"""

	def setUp(self):
		super().setUp()
		self.employee = frappe.db.get_value("Employee", {}, "name")
		if not self.employee:
			emp = frappe.get_doc({
				"doctype": "Employee",
				"employee_id": "TEST-EMP-001",
				"employee_name": "Test Maintenance Employee",
				"first_name": "Test",
				"last_name": "Employee",
				"status": "Active"
			})
			emp.insert(ignore_permissions=True)
			self.employee = emp.name

	def test_auto_create_issue_category(self):
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"title": "Voltage Spike Issue Test",
			"employee": self.employee,
			"ownership_type": "Organizational Asset",
			"maintenance_type": "IT",
			"equipment_category": "Electrical Equipment",
			"issue_category": "Voltage Spike Unique Auto Test",
			"equipment_name": "Generator B",
			"equipment_serial": "GEN-002-TEST",
			"priority": "High",
			"description": "Auto issue category test"
		})
		req.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Issue Category", "Voltage Spike Unique Auto Test"))
		self.assertEqual(req.issue_category, "Voltage Spike Unique Auto Test")

	def test_auto_handle_equipment(self):
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"title": "Chiller Unit Leak Test",
			"employee": self.employee,
			"ownership_type": "Organizational Asset",
			"maintenance_type": "IT",
			"equipment_category": "Building/Facility",
			"issue_category": "Water Leakage",
			"equipment_name": "Chiller Unit 5",
			"equipment_serial": "CHILLER-55-TEST",
			"priority": "Medium",
			"description": "Auto equipment creation test"
		})
		req.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Equipment", "CHILLER-55-TEST"))
		self.assertEqual(req.equipment, "CHILLER-55-TEST")

	def test_approval_status_and_work_order(self):
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"title": "HVAC Compressor Repair Test",
			"employee": self.employee,
			"ownership_type": "Organizational Asset",
			"maintenance_type": "IT",
			"equipment_category": "Building/Facility",
			"issue_category": "HVAC Breakdown",
			"equipment_name": "HVAC System Main",
			"equipment_serial": "HVAC-MAIN-TEST",
			"priority": "Critical",
			"description": "Work order test"
		})
		req.insert(ignore_permissions=True)
		req.approval_status = "Approved"
		req.save(ignore_permissions=True)
		self.assertIn(req.status, ["Approved", "In Progress", "Assigned"])

		wo_name = req.create_work_order()
		self.assertTrue(frappe.db.exists("Work Order", wo_name))

