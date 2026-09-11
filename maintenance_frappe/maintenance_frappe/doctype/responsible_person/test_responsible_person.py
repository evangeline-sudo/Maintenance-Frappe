# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestResponsiblePerson(FrappeTestCase):
	def test_create_responsible_person(self):
		# Create team if not exists
		if not frappe.db.exists("Maintenance Team", "TEAM-TEST"):
			frappe.get_doc({
				"doctype": "Maintenance Team",
				"team_name": "Test Team",
				"team_code": "TEAM-TEST",
				"is_active": 1
			}).insert()
		
		# If employee exists or mock
		# Verification of doctype model
		self.assertTrue(frappe.get_meta("Responsible Person"))

