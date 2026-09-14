import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from maintenance_frappe.maintenance_frappe.doctype.maintenance_request.maintenance_request import MaintenanceRequest


class TestMaintenanceRequest(FrappeTestCase):
	def test_organizational_maintenance_validation_and_cost(self):
		"""Test standard organizational maintenance flow and cost calculations"""
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
		doc.validate()
		self.assertEqual(doc.ownership_type, "Organizational Asset")
		self.assertEqual(doc.equipment_category, "IT Equipment")

		# Add work log with hourly rate
		doc.add_work_log(
			technician="tech@example.com",
			description="Inspected display connector",
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
		self.assertEqual(doc.total_parts_cost, 45.0)
		self.assertEqual(doc.total_maintenance_cost, 145.0)

	def test_non_organizational_maintenance_validation(self):
		"""Test non-organizational asset validation rules"""
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
			doc.validate()

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
			"description": "Routine quarterly filter cleaning",
			"employee": "EMP-00001",
			"priority": "High"
		})

		doc.validate()
		self.assertEqual(doc.ownership_type, "Non-Organizational Asset")
		self.assertEqual(doc.external_ownership_type, "Rented Equipment")
		self.assertEqual(doc.external_owner_name, "Cooling Solutions Inc.")
		self.assertEqual(doc.warranty_amc_status, "Under AMC")
