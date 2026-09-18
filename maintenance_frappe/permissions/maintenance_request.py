import frappe
from frappe import _


ALLOWED_ROLES = [
	"Employee",
	"Manager",
	"Maintenance Manager",
	"Maintenance User",
]


def get_permission_query_conditions(user=None):
	"""
	Return SQL conditions for Maintenance Request list queries.
	"""

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return "1=0"

	# Manager and Maintenance Manager can see all requests
	if any(role in user_roles for role in ["Manager", "Maintenance Manager"]):
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
		conditions.append(
			"(`tabMaintenance Request`.`owner` = {0})".format(
				frappe.db.escape(user)
			)
		)

	# Maintenance User can access their own requests and assigned requests
	if "Maintenance User" in user_roles:
		conditions.append(
			"(`tabMaintenance Request`.`owner` = {0})".format(
				frappe.db.escape(user)
			)
		)
		conditions.append(
			"(`tabMaintenance Request`.`assigned_to` = {0})".format(
				frappe.db.escape(user)
			)
		)

	if conditions:
		return " OR ".join(conditions)

	return "1=0"


def has_permission(doc=None, ptype=None, user=None, debug=False):
	"""
	Custom permission handler for Maintenance Request.
	Implements role-based access control.
	"""
	ptype = ptype or "read"

	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return False

	# Manager and Maintenance Manager have all permissions
	if any(role in user_roles for role in ["Manager", "Maintenance Manager"]):
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
			if doc.get("employee") == user or (employee and doc.get("employee") == employee):
				return True

	# Maintenance User can access their own and assigned requests
	if "Maintenance User" in user_roles:
		if ptype in ["read", "write", "create", "submit"]:
			if getattr(doc, "owner", None) == user or getattr(doc, "assigned_to", None) == user:
				return True

	return False


def has_app_permission(user=None):
	"""Check if user has permission to access the Maintenance app."""

	if not user:
		user = frappe.session.user

	if not user or user == "Guest":
		return False

	user_roles = frappe.get_roles(user)
	return any(role in ALLOWED_ROLES for role in user_roles)
