# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestEquipmentCategory(FrappeTestCase):
	def test_create_equipment_category(self):
		if not frappe.db.exists("Equipment Category", "Test Category"):
			category = frappe.get_doc({
				"doctype": "Equipment Category",
				"category_name": "Test Category",
				"description": "Category for testing",
				"is_active": 1
			}).insert()
			self.assertEqual(category.name, "Test Category")

