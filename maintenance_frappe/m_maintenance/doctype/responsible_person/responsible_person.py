# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ResponsiblePerson(Document):
	def validate(self):
		if not self.employee:
			frappe.throw(_("Employee is mandatory"))
		if not self.maintenance_team:
			frappe.throw(_("Maintenance Team is mandatory"))

