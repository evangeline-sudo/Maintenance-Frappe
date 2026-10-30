import frappe


def execute():
	"""Delete redundant desktop icons, ensure 'Maintenance' is visible for all employees, and hide extra workspaces."""
	try:
		frappe.db.sql("""
			DELETE FROM `tabDesktop Icon`
			WHERE name IN (
				'Maintenance-Frappe', 'Maintenance Frappe', 'maintenance_frappe',
				'Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management'
			)
			OR link_to IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
			OR label IN (
				'Maintenance-Frappe', 'Maintenance Frappe', 'maintenance_frappe',
				'Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management'
			)
			OR (app = 'maintenance_frappe' AND name != 'Maintenance' AND label != 'Maintenance')
		""")
		frappe.db.sql("""
			DELETE FROM `tabHas Role`
			WHERE parenttype = 'Desktop Icon'
			  AND parent IN (
				'Maintenance-Frappe', 'Maintenance Frappe', 'maintenance_frappe',
				'Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management'
			  )
		""")
		frappe.db.sql("""
			UPDATE `tabDesktop Icon`
			SET hidden = 0
			WHERE name = 'Maintenance'
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 1
			WHERE name IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 0
			WHERE name = 'Maintenance'
		""")
		frappe.db.commit()
	except Exception:
		pass

