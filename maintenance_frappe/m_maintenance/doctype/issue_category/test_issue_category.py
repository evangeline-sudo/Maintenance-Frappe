# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestIssueCategory(FrappeTestCase):
	def test_create_issue_category(self):
		if not frappe.db.exists("Issue Category", "HVAC Cooling Fault"):
			category = frappe.get_doc({
				"doctype": "Issue Category",
				"issue_category_name": "HVAC Cooling Fault",
				"description": "AC not cooling",
				"is_active": 1
			}).insert()
			self.assertEqual(category.name, "HVAC Cooling Fault")

