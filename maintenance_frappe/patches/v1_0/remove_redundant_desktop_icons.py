import frappe
from maintenance_frappe.api.maintenance import cleanup_redundant_desktop_icons_and_workspaces


def execute():
	"""Delete redundant desktop icons, ensure 'Maintenance' is visible for all employees, and configure Maintenance Workspace navigation."""
	cleanup_redundant_desktop_icons_and_workspaces()
