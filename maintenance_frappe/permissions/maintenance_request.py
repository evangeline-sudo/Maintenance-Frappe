import frappe
from frappe import _


ALLOWED_ROLES = [
	"Employee",
	"Manager",
	"Maintenance Manager",
	"Technician",
	"System Manager",
	"Administrator",
]


def get_permission_query_conditions(user=None):
	"""
	Return SQL conditions for Maintenance Request list queries.
	"""

	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	user_roles = frappe.get_roles(user)

	# System Manager, Administrator, Manager, and Maintenance Manager can see all requests
	if any(role in user_roles for role in ["System Manager", "Administrator", "Manager", "Maintenance Manager"]):
		return ""

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return "1=0"

	conditions = []
	escaped_user = frappe.db.escape(user)

	# Creator/Owner check for any logged-in user
	conditions.append("(`tabMaintenance Request`.`owner` = {0})".format(escaped_user))

	# Manager can see requests where they are assigned as manager
	if "Manager" in user_roles:
		conditions.append("(`tabMaintenance Request`.`manager` = {0})".format(escaped_user))

	# Technicians can see assigned requests
	if any(role in user_roles for role in ["Technician", "Maintenance Technician", "Maintenance User", "Supervisor"]):
		conditions.append("(`tabMaintenance Request`.`assigned_to` = {0})".format(escaped_user))

	# Employee can see their own requests linked via Employee record
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if employee:
		escaped_emp = frappe.db.escape(employee)
		conditions.append("(`tabMaintenance Request`.`employee` = {0})".format(escaped_emp))

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

	if user == "Administrator":
		return True

	user_roles = frappe.get_roles(user)

	# System Manager, Administrator, Manager, and Maintenance Manager have all permissions
	if any(role in user_roles for role in ["System Manager", "Administrator", "Manager", "Maintenance Manager"]):
		return True

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return False

	if not doc or isinstance(doc, str):
		return True

	# Creator/Owner can access their own request
	if getattr(doc, "owner", None) == user:
		return True

	# Manager can access requests where they are set as manager
	if "Manager" in user_roles and (getattr(doc, "manager", None) == user or getattr(doc, "unit_head", None) == user):
		return True

	# Technician / Maintenance User / Supervisor can access assigned requests
	if (
		any(role in user_roles for role in ["Technician", "Maintenance Technician", "Maintenance User", "Supervisor"])
		and getattr(doc, "assigned_to", None) == user
	):
		return True

	# Employee can access their own requests
	if "Employee" in user_roles:
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if ptype in ["read", "write", "create", "submit"]:
			if doc.get("employee") == user or (employee and doc.get("employee") == employee):
				return True

	return False


def has_app_permission(user=None):
	"""Check if user has permission to access the Maintenance app."""

	if not user:
		user = frappe.session.user

	if not user or user == "Guest":
		return False

	if user == "Administrator":
		return True

	user_roles = frappe.get_roles(user)
	return any(role in ALLOWED_ROLES for role in user_roles)

