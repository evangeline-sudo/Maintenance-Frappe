# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class UnitHeadApprovalConfiguration(Document):
	def validate(self):
		if self.approval_required and not self.unit_head:
			frappe.throw(_("Unit Head is mandatory when Approval Required is checked"))

