# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMaintenanceCause(FrappeTestCase):
	def test_create_maintenance_cause(self):
		if not frappe.db.exists("Maintenance Cause", "Power Surge"):
			cause = frappe.get_doc({
				"doctype": "Maintenance Cause",
				"cause_name": "Power Surge",
				"description": "Electrical issue",
				"is_active": 1
			}).insert()
			self.assertEqual(cause.name, "Power Surge")

