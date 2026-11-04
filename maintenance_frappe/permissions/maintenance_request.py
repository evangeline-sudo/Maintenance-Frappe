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


def get_reporting_employee_ids(user=None):
	"""
	Return all Employee IDs who directly or indirectly report to `user`.
	Also includes employees belonging to departments where `user` is the department head.
	"""
	if not user:
		user = frappe.session.user

	if not user or user == "Administrator":
		return []

	# 1. Find the Manager's own Employee record(s)
	manager_emps = frappe.get_all("Employee", filters={"user_id": user}, pluck="name")
	if not manager_emps:
		return []

	# 2. Direct and indirect reporting employees via 'reports_to'
	all_reports = set()
	current_level = set(manager_emps)
	while current_level:
		direct_reports = set(
			frappe.get_all(
				"Employee",
				filters={"reports_to": ["in", list(current_level)]},
				pluck="name"
			)
		)
		new_reports = direct_reports - all_reports
		if not new_reports:
			break
		all_reports |= new_reports
		current_level = new_reports

	# 3. Department head reports (if user or manager employee is set as head of department)
	try:
		dept_head_fields = []
		for f in ["custom_department_head", "head_of_department"]:
			if frappe.db.has_column("Department", f):
				dept_head_fields.append(f)

		for f in dept_head_fields:
			dept_names = frappe.get_all(
				"Department",
				filters={f: ["in", [user, *manager_emps]]},
				pluck="name"
			)
			if dept_names:
				dept_emps = frappe.get_all(
					"Employee",
					filters={"department": ["in", dept_names]},
					pluck="name"
				)
				all_reports.update(dept_emps)
	except Exception:
		pass

	# Exclude manager themselves
	all_reports.difference_update(manager_emps)
	return list(all_reports)


def get_reporting_user_ids(employee_ids):
	"""
	Return all user_ids linked to the given Employee IDs.
	"""
	if not employee_ids:
		return []

	users = frappe.get_all(
		"Employee",
		filters={"name": ["in", employee_ids]},
		pluck="user_id"
	)
	return [u for u in users if u]


def get_permission_query_conditions(user=None):
	"""
	Return SQL conditions for Maintenance Request list queries.
	- Maintenance Manager: full access across organization.
	- Manager: only requests submitted by their own reporting employees (and own requests).
	- Technician: assigned requests and own requests.
	- Employee: own requests.
	"""

	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""

	user_roles = frappe.get_roles(user)

	# System Manager, Administrator, and Maintenance Manager have all access to all maintenance requests across organization
	if any(role in user_roles for role in ["System Manager", "Administrator", "Maintenance Manager"]):
		return ""

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return "1=0"

	conditions = []
	escaped_user = frappe.db.escape(user)

	# Creator/Owner check for any logged-in user (can always see own requests)
	conditions.append("(`tabMaintenance Request`.`owner` = {0})".format(escaped_user))

	# Employee can see their own requests linked via Employee record
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if employee:
		escaped_emp = frappe.db.escape(employee)
		conditions.append("(`tabMaintenance Request`.`employee` = {0})".format(escaped_emp))

	# Manager: only Maintenance Requests submitted by their own reporting employees
	if "Manager" in user_roles:
		reporting_emp_ids = get_reporting_employee_ids(user)
		reporting_users = get_reporting_user_ids(reporting_emp_ids)

		manager_conditions = []
		if reporting_emp_ids:
			escaped_emp_ids = [frappe.db.escape(e) for e in reporting_emp_ids]
			manager_conditions.append(
				"`tabMaintenance Request`.`employee` IN ({0})".format(", ".join(escaped_emp_ids))
			)
		if reporting_users:
			escaped_user_ids = [frappe.db.escape(u) for u in reporting_users]
			manager_conditions.append(
				"`tabMaintenance Request`.`owner` IN ({0})".format(", ".join(escaped_user_ids))
			)

		if manager_conditions:
			conditions.append("({0})".format(" OR ".join(manager_conditions)))

	# Technicians can see assigned requests
	if any(role in user_roles for role in ["Technician", "Maintenance Technician", "Supervisor", "Maintenance User"]):
		conditions.append("(`tabMaintenance Request`.`assigned_to` = {0})".format(escaped_user))

	if conditions:
		return " OR ".join(conditions)

	return "1=0"


def has_permission(doc=None, ptype=None, user=None, debug=False):
	"""
	Custom permission handler for Maintenance Request.
	Implements role-based access control:
	- Maintenance Manager: full access across organization.
	- Manager: only requests submitted by their own reporting employees (and own requests).
	- Technician: assigned requests and own requests.
	- Employee: own requests.
	"""
	ptype = ptype or "read"

	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return True

	user_roles = frappe.get_roles(user)

	# System Manager, Administrator, and Maintenance Manager have all permissions across organization
	if any(role in user_roles for role in ["System Manager", "Administrator", "Maintenance Manager"]):
		return True

	if not any(role in user_roles for role in ALLOWED_ROLES):
		return False

	if not doc or isinstance(doc, str):
		return True

	# Creator/Owner can access their own request
	if getattr(doc, "owner", None) == user:
		return True

	# Employee can access their own requests
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if doc.get("employee") == user or (employee and doc.get("employee") == employee):
		return True

	# Manager: only Maintenance Requests submitted by their own reporting employees
	if "Manager" in user_roles:
		reporting_emp_ids = get_reporting_employee_ids(user)
		reporting_users = get_reporting_user_ids(reporting_emp_ids)

		doc_emp = doc.get("employee")
		doc_owner = doc.get("owner")

		if doc_emp and doc_emp in reporting_emp_ids:
			return True
		if doc_owner and doc_owner in reporting_users:
			return True

	# Technician / Maintenance Technician / Supervisor / Maintenance User can access assigned requests
	if (
		any(role in user_roles for role in ["Technician", "Maintenance Technician", "Supervisor", "Maintenance User"])
		and getattr(doc, "assigned_to", None) == user
	):
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

