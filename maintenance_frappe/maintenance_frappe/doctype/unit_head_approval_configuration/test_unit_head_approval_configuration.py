# Copyright (c) 2026, Evangeline and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestUnitHeadApprovalConfiguration(FrappeTestCase):
	def test_approval_configuration_validation(self):
		self.assertTrue(frappe.get_meta("Unit Head Approval Configuration"))

