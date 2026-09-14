# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMaintenanceTeam(FrappeTestCase):
	def test_create_maintenance_team(self):
		if not frappe.db.exists("Maintenance Team", "TEAM-ELEC"):
			team = frappe.get_doc({
				"doctype": "Maintenance Team",
				"team_name": "Electrical Team",
				"team_code": "TEAM-ELEC",
				"description": "Electrical maintenance team",
				"is_active": 1
			}).insert()
			self.assertEqual(team.name, "TEAM-ELEC")

