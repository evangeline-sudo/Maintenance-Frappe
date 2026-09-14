# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestProductTypeValue(FrappeTestCase):
	def test_create_product_type_value(self):
		if not frappe.db.exists("Product Type Value", "Electronics-Motherboard"):
			ptv = frappe.get_doc({
				"doctype": "Product Type Value",
				"product_type": "Electronics",
				"product_value": "Motherboard",
				"description": "Motherboards for PCs",
				"is_active": 1
			}).insert()
			self.assertEqual(ptv.name, "Electronics-Motherboard")

