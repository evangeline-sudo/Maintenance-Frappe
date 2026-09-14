import unittest
import frappe
from frappe.utils import now_datetime
from maintenance_frappe.maintenance_frappe.doctype.maintenance_request.maintenance_request import MaintenanceRequest


class TestMaintenanceRequest(unittest.TestCase):
	def setUp(self):
		frappe.db.rollback()

	def test_organizational_maintenance_lifecycle(self):
		"""Test standard organizational maintenance flow"""
		# Create test request
		doc = frappe.get_doc({
			"doctype": "Maintenance Request",
			"ownership_type": "Organizational Asset",
			"maintenance_type": "IT",
			"equipment_category": "IT Equipment",
			"title": "Laptop Screen Repair",
			"description": "Flickering display on company laptop",
			"employee": "EMP-00001",
			"priority": "Medium"
		})
		doc.insert(ignore_permissions=True)
		doc.submit()

		self.assertEqual(doc.ownership_type, "Organizational Asset")
		self.assertEqual(doc.status, "Approved")

		# Assign to technician
		doc.assign_to_technician("tech@example.com")
		self.assertEqual(doc.status, "Assigned")
		self.assertEqual(doc.assigned_to, "tech@example.com")

		# Start work
		doc.start_work()
		self.assertEqual(doc.status, "In Progress")

		# Save diagnosis
		doc.save_diagnosis(
			diagnosis_notes="Display connector loose, needs replacement cable",
			estimated_cost=150.0
		)
		self.assertEqual(doc.estimated_cost, 150.0)

		# Add work log with hourly rate
		doc.add_work_log(
			technician="tech@example.com",
			description="Inspected laptop motherboard and display ribbon cable",
			duration_minutes=120,
			hourly_rate=50.0
		)
		self.assertEqual(doc.total_labour_cost, 100.0)

		# Add parts used
		doc.append("parts_used", {
			"item": "Display-Cable-01",
			"item_name": "Display Ribbon Cable",
			"quantity": 1,
			"uom": "Nos",
			"rate": 45.0,
			"amount": 45.0
		})
		doc.calculate_total_costs()
		doc.save()

		self.assertEqual(doc.total_parts_cost, 45.0)
		self.assertEqual(doc.total_maintenance_cost, 145.0)

		# Mark resolved
		doc.mark_resolved(
			resolution_notes="Replaced ribbon cable and verified display output.",
			root_cause="Cable wear due to hinge friction."
		)
		self.assertEqual(doc.status, "Resolved")

		# Verify
		doc.verify_request("Verified", "Screen display working perfectly.")
		self.assertEqual(doc.verification_status, "Verified")

		# Close
		doc.close_request(closing_remarks="Closed after user verification.")
		self.assertEqual(doc.status, "Closed")

	def test_non_organizational_maintenance_validation(self):
		"""Test non-organizational asset validation rules"""
		# Missing external owner details should raise exception
		doc = frappe.get_doc({
			"doctype": "Maintenance Request",
			"ownership_type": "Non-Organizational Asset",
			"maintenance_type": "Non-IT",
			"equipment_category": "Electrical Equipment",
			"title": "Rented AC Servicing",
			"description": "AC cooling insufficient",
			"employee": "EMP-00001"
		})

		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_non_organizational_maintenance_success(self):
		"""Test valid non-organizational asset maintenance request"""
		doc = frappe.get_doc({
			"doctype": "Maintenance Request",
			"ownership_type": "Non-Organizational Asset",
			"external_ownership_type": "Rented Equipment",
			"external_owner_name": "Cooling Solutions Inc.",
			"external_contact_person": "John Doe",
			"external_contact_phone": "+1234567890",
			"contract_reference": "LEASE-2026-99",
			"warranty_amc_status": "Under AMC",
			"maintenance_type": "Non-IT",
			"equipment_category": "Electrical Equipment",
			"equipment_name": "Central Chiller AC Unit",
			"title": "Quarterly AMC Maintenance for Rented Chiller",
			"description": "Routine quarterly filter cleaning and gas pressure check",
			"employee": "EMP-00001",
			"priority": "High"
		})

		doc.insert(ignore_permissions=True)
		doc.submit()

		self.assertEqual(doc.ownership_type, "Non-Organizational Asset")
		self.assertEqual(doc.external_ownership_type, "Rented Equipment")
		self.assertEqual(doc.external_owner_name, "Cooling Solutions Inc.")
		self.assertEqual(doc.warranty_amc_status, "Under AMC")


if __name__ == "__main__":
	unittest.main()
