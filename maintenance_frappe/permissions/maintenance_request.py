import frappe
from frappe import _


ALLOWED_ROLES = [
	"All",
	"Employee",
	"Manager",
	"Maintenance Manager",
	"Maintenance User",
	"Technician",
	"Maintenance Technician",
	"Project Manager",
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

	# System Manager, Administrator, and Maintenance Manager have all access to all maintenance requests
	if any(role in user_roles for role in ["System Manager", "Administrator", "Maintenance Manager"]):
		return ""

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return "1=0"

	conditions = []
	escaped_user = frappe.db.escape(user)

	# Creator/Owner check for any logged-in user
	conditions.append("(`tabMaintenance Request`.`owner` = {0})".format(escaped_user))

	# Manager: approve when employee raised maintenance request (can see requests where they are manager/unit_head, or awaiting approval)
	if "Manager" in user_roles:
		manager_parts = []
		has_manager_col = False
		try:
			if hasattr(frappe, "db") and hasattr(frappe.db, "has_column"):
				has_manager_col = frappe.db.has_column("Maintenance Request", "manager")
			elif hasattr(frappe, "get_meta"):
				has_manager_col = frappe.get_meta("Maintenance Request").has_field("manager")
		except Exception:
			has_manager_col = False

		if has_manager_col:
			manager_parts.append("`tabMaintenance Request`.`manager` = {0}".format(escaped_user))

		has_unit_head = True
		try:
			if hasattr(frappe, "db") and hasattr(frappe.db, "has_column"):
				has_unit_head = frappe.db.has_column("Maintenance Request", "unit_head")
			elif hasattr(frappe, "get_meta"):
				has_unit_head = frappe.get_meta("Maintenance Request").has_field("unit_head")
		except Exception:
			has_unit_head = True

		if has_unit_head:
			manager_parts.append("`tabMaintenance Request`.`unit_head` = {0}".format(escaped_user))

		manager_parts.append("`tabMaintenance Request`.`approval_status` = 'Pending'")
		conditions.append("({0})".format(" OR ".join(manager_parts)))

	# Technicians can see assigned requests
	if any(role in user_roles for role in ["Technician", "Maintenance Technician", "Supervisor"]):
		conditions.append("(`tabMaintenance Request`.`assigned_to` = {0})".format(escaped_user))

	# Maintenance User can see assigned requests
	if "Maintenance User" in user_roles:
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

	# System Manager, Administrator, and Maintenance Manager have all permissions
	if any(role in user_roles for role in ["System Manager", "Administrator", "Maintenance Manager"]):
		return True

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return False

	if not doc or isinstance(doc, str):
		return True

	# Creator/Owner can access their own request
	if getattr(doc, "owner", None) == user:
		return True

	# Manager: can approve and access requests when employee raised them
	if "Manager" in user_roles:
		if (
			not getattr(doc, "manager", None)
			or getattr(doc, "manager", None) == user
			or getattr(doc, "unit_head", None) == user
			or getattr(doc, "approval_status", None) == "Pending"
		):
			return True

	# Technician / Maintenance Technician / Supervisor can access assigned requests
	if (
		any(role in user_roles for role in ["Technician", "Maintenance Technician", "Supervisor"])
		and getattr(doc, "assigned_to", None) == user
	):
		return True

	# Maintenance User can access their own or assigned requests
	if "Maintenance User" in user_roles:
		if getattr(doc, "assigned_to", None) == user or getattr(doc, "owner", None) == user:
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

