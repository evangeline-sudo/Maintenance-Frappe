# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Equipment(Document):
	def validate(self):
		if not self.equipment_id:
			frappe.throw(_("Equipment ID is mandatory"))
		if not self.equipment_name:
			frappe.throw(_("Equipment Name is mandatory"))
		if not self.equipment_category:
			frappe.throw(_("Equipment Category is mandatory"))
		
		# Validate that category is active
		if self.equipment_category:
			is_active = frappe.db.get_value("Equipment Category", self.equipment_category, "is_active")
			if is_active is not None and not is_active:
				frappe.throw(_("Selected Equipment Category {0} is inactive.").format(self.equipment_category))

		# Validate dates
		if self.purchase_date and self.warranty_expiry_date:
			if self.warranty_expiry_date < self.purchase_date:
				frappe.throw(_("Warranty Expiry Date cannot be before Purchase Date"))

