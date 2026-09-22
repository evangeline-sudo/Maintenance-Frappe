import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_datetime

class WorkOrder(Document):
	def validate(self):
		self.calculate_costs()
		self.calculate_downtime()

	def calculate_costs(self):
		p_cost = sum([flt(p.quantity) * flt(p.unit_cost) for p in self.parts_used])
		for p in self.parts_used:
			p.total_cost = flt(p.quantity) * flt(p.unit_cost)
		self.parts_cost = p_cost

		t_cost = sum([flt(t.hours_used) * flt(t.hourly_cost) for t in self.tools_used])
		for t in self.tools_used:
			t.total_cost = flt(t.hours_used) * flt(t.hourly_cost)
		self.tool_cost = t_cost

		self.total_cost = flt(self.labor_cost) + flt(self.parts_cost) + flt(self.tool_cost) + flt(self.vendor_cost)

	def calculate_downtime(self):
		if self.actual_start and self.actual_end:
			start = get_datetime(self.actual_start)
			end = get_datetime(self.actual_end)
			seconds = (end - start).total_seconds()
			self.downtime_hours = max(0.0, seconds / 3600.0)

	def on_submit(self):
		self.deduct_parts_stock()

	def deduct_parts_stock(self):
		for row in self.parts_used:
			if row.spare_part and frappe.db.exists("Maintenance Spare Part", row.spare_part):
				part_doc = frappe.get_doc("Maintenance Spare Part", row.spare_part)
				part_doc.quantity_available = max(0.0, flt(part_doc.quantity_available) - flt(row.quantity))
				part_doc.save(ignore_permissions=True)
