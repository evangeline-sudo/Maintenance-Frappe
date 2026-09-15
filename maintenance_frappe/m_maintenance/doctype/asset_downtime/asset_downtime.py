import frappe
from frappe.model.document import Document
from datetime import datetime

class AssetDowntime(Document):
	def validate(self):
		if self.downtime_start and self.downtime_end:
			start = frappe.utils.get_datetime(self.downtime_start)
			end = frappe.utils.get_datetime(self.downtime_end)
			diff_seconds = (end - start).total_seconds()
			self.total_downtime_hours = max(0.0, diff_seconds / 3600.0)
