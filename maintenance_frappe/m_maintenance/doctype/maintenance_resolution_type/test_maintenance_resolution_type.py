# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMaintenanceResolutionType(FrappeTestCase):
	def test_create_resolution_type(self):
		if not frappe.db.exists("Maintenance Resolution Type", "Component Replacement"):
			res = frappe.get_doc({
				"doctype": "Maintenance Resolution Type",
				"resolution_type": "Component Replacement",
				"description": "Replaced faulty part",
				"is_active": 1
			}).insert()
			self.assertEqual(res.name, "Component Replacement")

