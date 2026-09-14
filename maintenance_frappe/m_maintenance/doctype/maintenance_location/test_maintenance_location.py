# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMaintenanceLocation(FrappeTestCase):
	def test_create_location_hierarchy(self):
		campus = "Main Campus"
		if not frappe.db.exists("Maintenance Location", campus):
			frappe.get_doc({
				"doctype": "Maintenance Location",
				"location_name": campus,
				"location_type": "Campus",
				"is_active": 1
			}).insert()

		building = "Block A"
		if not frappe.db.exists("Maintenance Location", building):
			bldg_doc = frappe.get_doc({
				"doctype": "Maintenance Location",
				"location_name": building,
				"location_type": "Building",
				"parent_location": campus,
				"is_active": 1
			}).insert()
			self.assertEqual(bldg_doc.parent_location, campus)

