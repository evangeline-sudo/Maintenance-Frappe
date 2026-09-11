# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime, nowdate


class TestMaintenanceRequest(FrappeTestCase):
	def setUp(self):
		# Ensure test master data exists
		self.setup_masters()

	def setup_masters(self):
		# 1. Equipment Category
		if not frappe.db.exists("Equipment Category", "Test IT Equipment"):
			frappe.get_doc({
				"doctype": "Equipment Category",
				"category_name": "Test IT Equipment",
				"is_active": 1,
			}).insert()

		# 2. Issue Category
		if not frappe.db.exists("Issue Category", "Test Hardware Crash"):
			frappe.get_doc({
				"doctype": "Issue Category",
				"issue_category_name": "Test Hardware Crash",
				"equipment_category": "Test IT Equipment",
				"is_active": 1,
			}).insert()

		# Inactive Issue Category
		if not frappe.db.exists("Issue Category", "Test Inactive Issue"):
			frappe.get_doc({
				"doctype": "Issue Category",
				"issue_category_name": "Test Inactive Issue",
				"equipment_category": "Test IT Equipment",
				"is_active": 0,
			}).insert()

		# 3. Maintenance Team
		if not frappe.db.exists("Maintenance Team", "TEAM-IT"):
			frappe.get_doc({
				"doctype": "Maintenance Team",
				"team_name": "IT Support Team",
				"team_code": "TEAM-IT",
				"is_active": 1,
			}).insert()

		if not frappe.db.exists("Maintenance Team", "TEAM-MECH"):
			frappe.get_doc({
				"doctype": "Maintenance Team",
				"team_name": "Mechanical Team",
				"team_code": "TEAM-MECH",
				"is_active": 1,
			}).insert()

		# 4. Location
		if not frappe.db.exists("Maintenance Location", "Main Lab"):
			frappe.get_doc({
				"doctype": "Maintenance Location",
				"location_name": "Main Lab",
				"location_type": "Lab",
				"is_active": 1,
			}).insert()

		# 5. Maintenance Cause
		if not frappe.db.exists("Maintenance Cause", "Wear and Tear"):
			frappe.get_doc({
				"doctype": "Maintenance Cause",
				"cause_name": "Wear and Tear",
				"is_active": 1,
			}).insert()

		# 6. Maintenance Resolution Type
		if not frappe.db.exists("Maintenance Resolution Type", "Part Replaced"):
			frappe.get_doc({
				"doctype": "Maintenance Resolution Type",
				"resolution_type": "Part Replaced",
				"is_active": 1,
			}).insert()

		# 7. Equipment
		if not frappe.db.exists("Equipment", "EQP-TEST-ACTIVE"):
			frappe.get_doc({
				"doctype": "Equipment",
				"equipment_id": "EQP-TEST-ACTIVE",
				"equipment_name": "Server Unit 1",
				"equipment_category": "Test IT Equipment",
				"location": "Main Lab",
				"status": "Active",
			}).insert()

		if not frappe.db.exists("Equipment", "EQP-TEST-RETIRED"):
			frappe.get_doc({
				"doctype": "Equipment",
				"equipment_id": "EQP-TEST-RETIRED",
				"equipment_name": "Old Server Unit",
				"equipment_category": "Test IT Equipment",
				"location": "Main Lab",
				"status": "Retired",
			}).insert()

		# 8. Employee (if Employee doctype is available, or ensure test employee exists)
		self.employee = self.get_or_create_test_employee("EMP-MAINT-001", "John Requester")
		self.unit_head = self.get_or_create_test_employee("EMP-MAINT-002", "Jane UnitHead")
		self.technician_emp = self.get_or_create_test_employee("EMP-MAINT-003", "Bob Technician")
		self.other_technician_emp = self.get_or_create_test_employee("EMP-MAINT-004", "Alice Mech")

		# 9. Responsible Person
		if not frappe.db.exists("Responsible Person", self.technician_emp):
			frappe.get_doc({
				"doctype": "Responsible Person",
				"employee": self.technician_emp,
				"maintenance_team": "TEAM-IT",
				"specialization": "Test Hardware Crash",
				"is_active": 1,
			}).insert()

		if not frappe.db.exists("Responsible Person", self.other_technician_emp):
			frappe.get_doc({
				"doctype": "Responsible Person",
				"employee": self.other_technician_emp,
				"maintenance_team": "TEAM-MECH",
				"is_active": 1,
			}).insert()

	def get_or_create_test_employee(self, emp_id, emp_name):
		if frappe.db.exists("DocType", "Employee"):
			if not frappe.db.exists("Employee", emp_id):
				try:
					doc = frappe.get_doc({
						"doctype": "Employee",
						"name": emp_id,
						"employee": emp_id,
						"first_name": emp_name,
						"employee_name": emp_name,
						"status": "Active",
					}).insert(ignore_permissions=True, ignore_mandatory=True)
					return doc.name
				except Exception:
					# Return existing or fallback
					existing = frappe.db.get_value("Employee", {}, "name")
					return existing or emp_id
			return emp_id
		return emp_id

	def test_01_create_request_without_approval(self):
		"""Request without matching approval rule defaults to Approved."""
		# Ensure no approval rule for priority Low
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Breakdown",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-ACTIVE",
			"priority": "Low",
			"description": "System fan is making rattling noise.",
		}).insert()

		self.assertEqual(req.approval_required, 0)
		self.assertEqual(req.approval_status, "Not Required")
		self.assertEqual(req.status, "Approved")
		self.assertTrue(len(req.status_history) >= 1)

	def test_02_create_request_with_conditional_approval(self):
		"""Request matching approval rule enters Pending Approval status."""
		# Create approval rule for Critical priority
		rule_name = "Rule-Critical-Crash"
		if not frappe.db.exists("Unit Head Approval Configuration", rule_name):
			frappe.get_doc({
				"doctype": "Unit Head Approval Configuration",
				"configuration_name": rule_name,
				"issue_category": "Test Hardware Crash",
				"priority": "Critical",
				"approval_required": 1,
				"unit_head": self.unit_head,
				"is_active": 1,
			}).insert()

		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Breakdown",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-ACTIVE",
			"priority": "Critical",
			"description": "Complete production server crash.",
		}).insert()

		self.assertEqual(req.approval_required, 1)
		self.assertEqual(req.approval_status, "Pending")
		self.assertEqual(req.unit_head, self.unit_head)
		self.assertEqual(req.status, "Pending Approval")

		# Test Unit Head Approval
		req.approve_request(remarks="Approved for immediate maintenance")
		self.assertEqual(req.approval_status, "Approved")
		self.assertEqual(req.status, "Approved")

	def test_03_rejection_workflow(self):
		"""Unit Head rejection requires remarks and transitions to Rejected."""
		rule_name = "Rule-Critical-Crash"
		if not frappe.db.exists("Unit Head Approval Configuration", rule_name):
			frappe.get_doc({
				"doctype": "Unit Head Approval Configuration",
				"configuration_name": rule_name,
				"issue_category": "Test Hardware Crash",
				"priority": "Critical",
				"approval_required": 1,
				"unit_head": self.unit_head,
				"is_active": 1,
			}).insert()

		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Breakdown",
			"issue_category": "Test Hardware Crash",
			"priority": "Critical",
			"description": "Minor glitch reported as critical.",
		}).insert()

		# Rejection without remarks should throw error
		self.assertRaises(frappe.ValidationError, req.reject_request, remarks="")

		# Rejection with remarks
		req.reject_request(remarks="Not a critical breakdown. Please submit as regular ticket.")
		self.assertEqual(req.approval_status, "Rejected")
		self.assertEqual(req.status, "Rejected")

	def test_04_admin_assignment_validations(self):
		"""Admin assigns team and technician with strict team matching."""
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Repair",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-ACTIVE",
			"priority": "Medium",
			"description": "Hard drive diagnostic required.",
		}).insert()

		# Try to assign technician from TEAM-MECH while assigning TEAM-IT
		self.assertRaises(
			frappe.ValidationError,
			req.assign_technician,
			team="TEAM-IT",
			technician=self.other_technician_emp,
			expected_date=add_days(nowdate(), 2),
			remarks="Assigning IT task to Mech tech",
		)

		# Valid assignment
		req.assign_technician(
			team="TEAM-IT",
			technician=self.technician_emp,
			expected_date=add_days(nowdate(), 2),
			remarks="Assigned to IT technician",
		)
		self.assertEqual(req.status, "Assigned")
		self.assertEqual(req.assigned_team, "TEAM-IT")
		self.assertEqual(req.responsible_person, self.technician_emp)

	def test_05_technician_processing_and_resolution(self):
		"""Technician starts work, logs child records, and resolves."""
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Repair",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-ACTIVE",
			"priority": "Medium",
			"description": "Network adapter replacement.",
		}).insert()

		req.assign_technician(team="TEAM-IT", technician=self.technician_emp)

		# Technician starts work
		req.start_maintenance_work()
		self.assertEqual(req.status, "In Progress")
		self.assertIsNotNone(req.work_start_date)

		# Add Parts Used and Work Log child records
		req.append("parts_used", {
			"part_name": "Gigabit Ethernet Card",
			"quantity": 1,
			"unit": "Nos",
			"remarks": "Replaced burned network card",
		})
		req.append("work_logs", {
			"technician": self.technician_emp,
			"work_date": nowdate(),
			"work_type": "Replacement",
			"time_spent": 1.5,
			"work_status": "Completed",
			"remarks": "Replaced NIC card and ran diagnostic ping tests.",
		})
		req.save()

		# Attempt resolution without mandatory fields should fail
		self.assertRaises(
			frappe.ValidationError,
			req.resolve_maintenance,
			resolution_type="",
			resolution_details="",
			diagnosis="",
			work_details="",
		)

		# Valid resolution
		req.resolve_maintenance(
			resolution_type="Part Replaced",
			resolution_details="New PCIe NIC card installed and configured.",
			diagnosis="Network chip burnt due to power surge.",
			work_details="Replaced NIC, updated drivers, tested connection.",
			failure_cause="Wear and Tear",
		)
		self.assertEqual(req.status, "Resolved")
		self.assertIsNotNone(req.work_completion_date)

	def test_06_verification_and_rework_workflow(self):
		"""Supervisor can request rework or verify and close."""
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Repair",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-ACTIVE",
			"priority": "Medium",
			"description": "Display flickering.",
		}).insert()

		req.assign_technician(team="TEAM-IT", technician=self.technician_emp)
		req.start_maintenance_work()
		req.resolve_maintenance(
			resolution_type="Part Replaced",
			resolution_details="Cable re-seated.",
			diagnosis="Loose display connector cable.",
			work_details="Secured display cable.",
			failure_cause="Wear and Tear",
		)
		self.assertEqual(req.status, "Resolved")

		# Supervisor requests Rework
		req.request_rework(remarks="Display still flickers at high resolutions. Please re-check.")
		self.assertEqual(req.status, "In Progress")
		self.assertEqual(req.verification_status, "Rework Required")
		self.assertEqual(req.reopen_count, 1)

		# Technician resolves again
		req.resolve_maintenance(
			resolution_type="Part Replaced",
			resolution_details="Replaced HDMI ribbon cable.",
			diagnosis="Cable damaged internally.",
			work_details="Installed new HDMI ribbon cable.",
			failure_cause="Wear and Tear",
		)
		self.assertEqual(req.status, "Resolved")

		# Supervisor verifies and closes
		req.verify_and_close(remarks="Verified, display is steady now.")
		self.assertEqual(req.status, "Closed")
		self.assertEqual(req.verification_status, "Accepted")
		self.assertIsNotNone(req.verification_date)

	def test_07_retired_equipment_validation(self):
		"""Retired equipment cannot be selected for maintenance requests."""
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Breakdown",
			"issue_category": "Test Hardware Crash",
			"equipment": "EQP-TEST-RETIRED",
			"description": "Trying to maintain retired machine.",
		})
		self.assertRaises(frappe.ValidationError, req.insert)

	def test_08_inactive_category_validation(self):
		"""Inactive issue category cannot be selected."""
		req = frappe.get_doc({
			"doctype": "Maintenance Request",
			"employee": self.employee,
			"request_type": "Breakdown",
			"issue_category": "Test Inactive Issue",
			"description": "Using inactive category.",
		})
		self.assertRaises(frappe.ValidationError, req.insert)

