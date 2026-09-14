# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MaintenanceTeam(Document):
	def validate(self):
		if not self.team_name:
			frappe.throw(_("Team Name is mandatory"))
		if not self.team_code:
			frappe.throw(_("Team Code is mandatory"))

