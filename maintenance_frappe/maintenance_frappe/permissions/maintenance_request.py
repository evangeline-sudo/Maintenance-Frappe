import frappe
from frappe import _


def has_permission(doc, perm_type, user):
	"""
	Custom permission handler for Maintenance Request
	Implements role-based access control
	"""
	if not doc:
		return False

	# Admin has all permissions
	if "Administrator" in frappe.get_roles(user):
		return True

	# Employee can only see their own requests
	if "Employee" in frappe.get_roles(user):
		if perm_type == "read":
			return doc.employee == user or doc.employee == frappe.db.get_value("User", user, "employee")
		if perm_type == "write":
			return doc.employee == user or doc.employee == frappe.db.get_value("User", user, "employee")
		if perm_type == "submit":
			return doc.employee == user or doc.employee == frappe.db.get_value("User", user, "employee")

	# Unit Head can approve requests for their unit
	if "Unit Head" in frappe.get_roles(user):
		if perm_type in ["read", "write"]:
			return doc.unit_head == user or doc.unit == frappe.db.get_value("User", user, "unit")
		if perm_type == "approve":
			return doc.unit_head == user

	# Technician can only see and work on assigned requests
	if "Technician" in frappe.get_roles(user):
		if perm_type in ["read", "write"]:
			return doc.assigned_to == user

	# Supervisor can read all and close requests
	if "Supervisor" in frappe.get_roles(user):
		if perm_type == "read":
			return True
		if perm_type in ["write", "close"]:
			return True

	return False


def has_app_permission(user):
	"""Check if user has permission to access the Maintenance app"""
	allowed_roles = ["Administrator", "Employee", "Unit Head", "Technician", "Supervisor"]
	user_roles = frappe.get_roles(user)
	return any(role in allowed_roles for role in user_roles)
