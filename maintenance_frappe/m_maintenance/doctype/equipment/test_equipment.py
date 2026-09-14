# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestEquipment(FrappeTestCase):
	def setUp(self):
		if not frappe.db.exists("Equipment Category", "IT Assets"):
			frappe.get_doc({
				"doctype": "Equipment Category",
				"category_name": "IT Assets",
				"is_active": 1
			}).insert()

	def test_create_equipment(self):
		eq_id = "EQP-TEST-001"
		if not frappe.db.exists("Equipment", eq_id):
			eq = frappe.get_doc({
				"doctype": "Equipment",
				"equipment_id": eq_id,
				"equipment_name": "Dell OptiPlex 7090",
				"equipment_category": "IT Assets",
				"criticality": "High",
				"status": "Active"
			}).insert()
			self.assertEqual(eq.name, eq_id)

