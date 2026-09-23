import frappe


def execute():
	"""Delete redundant desktop icons and hide extra workspaces."""
	try:
		frappe.db.sql("""
			DELETE FROM `tabDesktop Icon`
			WHERE name IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
			   OR link_to IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
			   OR label IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 1
			WHERE name IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
		""")
		frappe.db.commit()
	except Exception:
		pass

