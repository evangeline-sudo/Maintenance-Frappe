import frappe
from frappe import _


def get_permission_query_conditions(user=None):
	"""
	Return SQL conditions for Maintenance Request list queries.
	"""

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)

	# Manager, Administrator, System Manager, and Supervisor can see all requests
	if any(role in user_roles for role in ["Administrator", "System Manager", "Maintenance Manager", "Supervisor"]):
		return ""

	conditions = []

	# Employee can see their own requests
	if "Employee" in user_roles:
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if employee:
			conditions.append(
				"(`tabMaintenance Request`.`employee` = {0})".format(
					frappe.db.escape(employee)
				)
			)
		# Also check by owner/user
		conditions.append(
			"(`tabMaintenance Request`.`owner` = {0})".format(
				frappe.db.escape(user)
			)
		)

	# Unit Head can see requests assigned to their unit
	if "Unit Head" in user_roles:
		unit = frappe.db.get_value("Employee", {"user_id": user}, "custom_unit")
		if unit:
			conditions.append(
				"(`tabMaintenance Request`.`unit` = {0})".format(
					frappe.db.escape(unit)
				)
			)

	# Technician can see requests assigned to them
	if "Maintenance Technician" in user_roles:
		conditions.append(
			"(`tabMaintenance Request`.`assigned_to` = {0})".format(
				frappe.db.escape(user)
			)
		)

	# If the user has one or more allowed conditions
	if conditions:
		return " OR ".join(conditions)

	# Fallback: allow if owner
	return "(`tabMaintenance Request`.`owner` = {0})".format(frappe.db.escape(user))


def has_permission(doc=None, ptype=None, user=None, debug=False):
	"""
	Custom permission handler for Maintenance Request.
	Implements role-based access control.
	"""
	ptype = ptype or "read"

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)

	# Managers & Admins have all permissions
	if any(role in user_roles for role in ["Administrator", "System Manager", "Maintenance Manager", "Supervisor"]):
		return True

	if not doc or isinstance(doc, str):
		return True

	# Creator/Owner can access their own request
	if getattr(doc, "owner", None) == user:
		return True

	# Employee can access their own requests
	if "Employee" in user_roles:
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if ptype in ["read", "write", "create", "submit"]:
			if doc.employee == user or (employee and doc.employee == employee):
				return True

	# Unit Head can access requests for their unit
	if "Unit Head" in user_roles:
		unit = frappe.db.get_value("Employee", {"user_id": user}, "custom_unit")
		if ptype in ["read", "write", "select"]:
			if (doc.get("unit_head") and doc.unit_head == user) or (unit and doc.get("unit") and doc.unit == unit):
				return True
		if ptype == "approve":
			if doc.get("unit_head") and doc.unit_head == user:
				return True

	# Technician can access assigned requests
	if "Maintenance Technician" in user_roles:
		if ptype in ["read", "write"]:
			if doc.get("assigned_to") and doc.assigned_to == user:
				return True

	return False


def has_app_permission(user=None):
	"""Check if user has permission to access the Maintenance app."""

	if not user:
		user = frappe.session.user

	if not user or user == "Guest":
		return False

	allowed_roles = [
		"Administrator",
		"System Manager",
		"Maintenance Manager",
		"Employee",
		"Unit Head",
		"Maintenance Technician",
		"Supervisor",
		"Maintenance User",
		"All",
	]

	user_roles = frappe.get_roles(user)

	return any(role in allowed_roles for role in user_roles)
