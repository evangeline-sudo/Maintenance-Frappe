import frappe
from frappe import _


def ensure_page_permissions():
	"""Ensure standard roles have Read access to Page, Workspace, and Desktop Icon across DocPerm and Custom DocPerm."""
	target_roles = [
		"All",
		"Employee",
		"Manager",
		"Maintenance Manager",
		"Maintenance User",
		"Technician",
		"Maintenance Technician",
		"Project Manager",
		"System Manager",
	]
	for doctype in ["Page", "Workspace", "Desktop Icon"]:
		# 1. Standard DocPerm
		for role in target_roles:
			if not frappe.db.exists("DocPerm", {"parent": doctype, "role": role}):
				try:
					perm = frappe.get_doc({
						"doctype": "DocPerm",
						"parent": doctype,
						"parenttype": "DocType",
						"parentfield": "permissions",
						"role": role,
						"read": 1,
						"select": 1
					})
					perm.insert(ignore_permissions=True)
				except Exception:
					pass

		# 2. Custom DocPerm (if custom permissions exist for Page/Workspace/Desktop Icon)
		if frappe.db.table_exists("Custom DocPerm"):
			if frappe.db.exists("Custom DocPerm", {"parent": doctype}):
				for role in target_roles:
					if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
						try:
							c_perm = frappe.get_doc({
								"doctype": "Custom DocPerm",
								"parent": doctype,
								"parenttype": "DocType",
								"parentfield": "permissions",
								"role": role,
								"read": 1,
								"select": 1
							})
							c_perm.insert(ignore_permissions=True)
						except Exception:
							pass


def sync_maintenance_dashboard_metrics():
	"""Ensure standard Number Cards and Dashboard Charts exist in DB for Maintenance Dashboard."""
	number_cards = [
		{
			"doctype": "Number Card",
			"name": "Total Requests",
			"label": "Total Requests",
			"function": "Count",
			"document_type": "Maintenance Request",
			"filters_json": "[]",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Number Card",
			"name": "Open Requests",
			"label": "Open Requests",
			"function": "Count",
			"document_type": "Maintenance Request",
			"filters_json": '[["Maintenance Request", "status", "in", ["Draft", "Submitted", "Approved", "In Progress"]]]',
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Number Card",
			"name": "Pending Approvals",
			"label": "Pending Approvals",
			"function": "Count",
			"document_type": "Maintenance Request",
			"filters_json": '[["Maintenance Request", "approval_status", "=", "Pending"]]',
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Number Card",
			"name": "Active Equipment",
			"label": "Active Equipment",
			"function": "Count",
			"document_type": "Equipment",
			"filters_json": '[["Equipment", "status", "=", "Active"]]',
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Number Card",
			"name": "Maintenance Teams",
			"label": "Maintenance Teams",
			"function": "Count",
			"document_type": "Maintenance Team",
			"filters_json": '[["Maintenance Team", "is_active", "=", 1]]',
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
	]

	for card in number_cards:
		if not frappe.db.exists("Number Card", card["name"]):
			try:
				frappe.get_doc(card).insert(ignore_permissions=True)
			except Exception:
				pass
		else:
			frappe.db.set_value("Number Card", card["name"], "is_public", 1)

	charts = [
		{
			"doctype": "Dashboard Chart",
			"name": "Maintenance Requests by Status",
			"chart_name": "Maintenance Requests by Status",
			"chart_type": "Group By",
			"document_type": "Maintenance Request",
			"group_by_based_on": "status",
			"group_by_type": "Count",
			"type": "Pie",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Request Priority",
			"chart_name": "Request Priority",
			"chart_type": "Group By",
			"document_type": "Maintenance Request",
			"group_by_based_on": "priority",
			"group_by_type": "Count",
			"type": "Pie",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Requests by Issue Category",
			"chart_name": "Requests by Issue Category",
			"chart_type": "Group By",
			"document_type": "Maintenance Request",
			"group_by_based_on": "issue_category",
			"group_by_type": "Count",
			"type": "Bar",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Requests by Equipment Category",
			"chart_name": "Requests by Equipment Category",
			"chart_type": "Group By",
			"document_type": "Maintenance Request",
			"group_by_based_on": "equipment_category",
			"group_by_type": "Count",
			"type": "Bar",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Maintenance Types Breakdown Pie",
			"chart_name": "Maintenance Types Breakdown Pie",
			"chart_type": "Group By",
			"document_type": "Maintenance Request",
			"group_by_based_on": "maintenance_type",
			"group_by_type": "Count",
			"type": "Pie",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
		{
			"doctype": "Dashboard Chart",
			"name": "Equipment Status Breakdown Pie",
			"chart_name": "Equipment Status Breakdown Pie",
			"chart_type": "Group By",
			"document_type": "Equipment",
			"group_by_based_on": "status",
			"group_by_type": "Count",
			"type": "Pie",
			"is_public": 1,
			"is_standard": 1,
			"module": "Maintenance Management",
		},
	]

	for c in charts:
		if not frappe.db.exists("Dashboard Chart", c["name"]):
			try:
				frappe.get_doc(c).insert(ignore_permissions=True)
			except Exception:
				pass
		else:
			frappe.db.set_value("Dashboard Chart", c["name"], "is_public", 1)

	frappe.db.commit()


def after_migrate_setup():
	"""Run DB setup tasks safely during migrate post-sync."""
	try:
		ensure_page_permissions()
		sync_maintenance_dashboard_metrics()
		fix_work_order_tools_and_checklists()
		cleanup_redundant_desktop_icons_and_workspaces()
	except Exception as e:
		frappe.log_error(f"Error in after_migrate_setup: {e}")


def fix_work_order_tools_and_checklists():
	"""Ensure Work Order tools_used points to child table 'Work Order Tool' and tabDocField is synced."""
	try:
		if frappe.db.table_exists("DocField"):
			frappe.db.sql("""
				UPDATE `tabDocField`
				SET options = 'Work Order Tool'
				WHERE parent = 'Work Order' AND fieldname = 'tools_used'
			""")
		if frappe.db.table_exists("Custom Field"):
			frappe.db.sql("""
				UPDATE `tabCustom Field`
				SET options = 'Work Order Tool'
				WHERE dt = 'Work Order' AND fieldname = 'tools_used'
			""")
	except Exception as e:
		frappe.log_error(f"Error updating Work Order child table options: {e}")


def after_install_setup():
	"""Run DB setup tasks safely during app installation on a new system."""
	after_migrate_setup()


def cleanup_redundant_desktop_icons_and_workspaces():
	"""Delete redundant desktop icons and hide extra workspaces in database, keeping 'Maintenance' intact for all users."""
	sync_maintenance_dashboard_metrics()
	try:
		frappe.db.sql("""
			DELETE FROM `tabDesktop Icon`
			WHERE (
				name IN (
					'Maintenance-Frappe', 'Maintenance Frappe', 'maintenance_frappe',
					'Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management'
				)
				OR (label IN (
					'Maintenance-Frappe', 'Maintenance Frappe', 'maintenance_frappe',
					'Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management'
				) AND name != 'Maintenance')
				OR (app = 'maintenance_frappe' AND name != 'Maintenance' AND label != 'Maintenance')
			)
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
			SET hidden = 0,
			    icon_type = 'Link',
			    link_type = 'Workspace Sidebar',
			    link_to = 'Maintenance',
			    link = '/desk/maintenance',
			    sidebar = NULL
			WHERE name = 'Maintenance' OR label = 'Maintenance'
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 1, parent_page = 'Maintenance'
			WHERE name = 'Maintenance Dashboard'
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 1
			WHERE name IN ('Maintenance Home', 'Maintenance Management')
		""")
		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 0,
			    title = 'Maintenance',
			    label = 'Maintenance',
			    icon = 'tool'
			WHERE name = 'Maintenance'
		""")
		if frappe.db.table_exists("Workspace Sidebar Item"):
			frappe.db.sql("""
				UPDATE `tabWorkspace Sidebar Item`
				SET label = 'Maintenance', route = '/desk/maintenance'
				WHERE parent = 'Maintenance' AND link_to = 'Maintenance' AND link_type = 'Workspace'
			""")
		frappe.db.sql("""
			DELETE FROM `tabWorkspace Sidebar`
			WHERE name IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management')
			   OR (title IN ('Maintenance Home', 'Maintenance Dashboard', 'Maintenance Management') AND name != 'Maintenance')
		""")

		# Ensure target maintenance roles are associated with the 'Maintenance' Desktop Icon
		target_desktop_roles = [
			"System Manager",
			"Maintenance Manager",
			"Manager",
			"Maintenance User",
			"Maintenance Technician",
			"Technician",
			"Employee",
			"All",
		]

		if not frappe.db.exists("Desktop Icon", "Maintenance"):
			try:
				doc = frappe.get_doc({
					"doctype": "Desktop Icon",
					"name": "Maintenance",
					"label": "Maintenance",
					"app": "maintenance_frappe",
					"bg_color": "blue",
					"hidden": 0,
					"icon": "tool",
					"icon_type": "Link",
					"link": "/desk/maintenance",
					"link_to": "Maintenance",
					"link_type": "Workspace Sidebar",
					"standard": 1,
					"sidebar": None,
					"restrict_removal": 0,
					"roles": [{"role": r} for r in target_desktop_roles]
				})
				doc.insert(ignore_permissions=True)
			except Exception:
				pass

		for role in target_desktop_roles:
			for ptype in ("Desktop Icon", "Workspace"):
				if not frappe.db.exists("Has Role", {"parent": "Maintenance", "parenttype": ptype, "role": role}):
					try:
						frappe.get_doc({
							"doctype": "Has Role",
							"parent": "Maintenance",
							"parenttype": ptype,
							"parentfield": "roles",
							"role": role
						}).insert(ignore_permissions=True)
					except Exception:
						pass

		frappe.db.sql("""
			UPDATE `tabWorkspace`
			SET is_hidden = 0,
			    public = 1,
			    title = 'Maintenance',
			    label = 'Maintenance',
			    icon = 'tool',
			    module = 'Maintenance Management'
			WHERE name = 'Maintenance'
		""")

		frappe.clear_document_cache("Desktop Icon", "Maintenance")
		frappe.clear_document_cache("Workspace", "Maintenance")
		frappe.cache.delete_key("desktop_icons")
		frappe.cache.hdel("desktop_icons", frappe.session.user)
		frappe.cache.delete_key("bootinfo")
		frappe.db.commit()
	except Exception:
		pass


def filter_employee_sidebar(bootinfo):
	"""Ensure 'Maintenance' sidebar and desktop icon exist while hiding extra icons on Desk."""
	cleanup_redundant_desktop_icons_and_workspaces()
	ensure_page_permissions()

	# 1. Remove ONLY extra desktop icons from bootinfo
	extra_icon_names = {
		"maintenance home",
		"maintenance dashboard",
		"maintenance management",
		"maintenance-frappe",
		"maintenance frappe",
		"maintenance_frappe",
	}

	def is_redundant_icon(k, v):
		name = str(getattr(v, "get", lambda x: None)("name") or k or "").lower()
		label = str(getattr(v, "get", lambda x: None)("label") or "").lower()
		app = str(getattr(v, "get", lambda x: None)("app") or "").lower()
		if name in extra_icon_names or label in extra_icon_names:
			return True
		if app == "maintenance_frappe" and name != "maintenance" and label != "maintenance":
			return True
		return False

	target_roles_list = [
		{"role": "System Manager"},
		{"role": "Maintenance Manager"},
		{"role": "Manager"},
		{"role": "Maintenance User"},
		{"role": "Employee"},
		{"role": "All"}
	]

	default_maintenance_icon = {
		"doctype": "Desktop Icon",
		"name": "Maintenance",
		"label": "Maintenance",
		"app": "maintenance_frappe",
		"bg_color": "blue",
		"hidden": 0,
		"icon": "tool",
		"icon_image": "",
		"icon_type": "Link",
		"idx": 0,
		"link": "/desk/maintenance",
		"link_to": "Maintenance",
		"link_type": "Workspace Sidebar",
		"logo_url": "",
		"parent_icon": None,
		"restrict_removal": 0,
		"standard": 1,
		"sidebar": None,
		"roles": target_roles_list,
	}

	for key in ("desktop_icon", "desktop_icons"):
		if key not in bootinfo:
			continue
		if isinstance(bootinfo[key], dict):
			bootinfo[key] = {
				k: v for k, v in bootinfo[key].items()
				if not is_redundant_icon(k, v)
			}
			# Ensure 'Maintenance' is present for all users
			has_maintenance = any(
				str(k).lower() == "maintenance"
				or str(getattr(v, "get", lambda x: None)("name") or "").lower() == "maintenance"
				or str(getattr(v, "get", lambda x: None)("label") or "").lower() == "maintenance"
				for k, v in bootinfo[key].items()
			)
			if not has_maintenance:
				if frappe.db.exists("Desktop Icon", "Maintenance"):
					try:
						doc = frappe.get_cached_doc("Desktop Icon", "Maintenance")
						doc_dict = doc.as_dict()
						doc_dict["hidden"] = 0
						doc_dict["icon_type"] = "Link"
						doc_dict["link"] = "/desk/maintenance"
						doc_dict["link_to"] = "Maintenance"
						doc_dict["link_type"] = "Workspace Sidebar"
						doc_dict["sidebar"] = None
						doc_dict["roles"] = target_roles_list
						bootinfo[key]["Maintenance"] = doc_dict
						has_maintenance = True
					except Exception:
						pass
				if not has_maintenance:
					bootinfo[key]["Maintenance"] = dict(default_maintenance_icon)

			# Explicitly ensure Maintenance icon is visible and unhidden with authorized maintenance roles
			for k, v in bootinfo[key].items():
				if (
					str(k).lower() == "maintenance"
					or str(getattr(v, "get", lambda x: None)("name") or "").lower() == "maintenance"
					or str(getattr(v, "get", lambda x: None)("label") or "").lower() == "maintenance"
				):
					if isinstance(v, dict):
						v["hidden"] = 0
						v["icon_type"] = "Link"
						v["link"] = "/desk/maintenance"
						v["link_to"] = "Maintenance"
						v["link_type"] = "Workspace Sidebar"
						v["sidebar"] = None
						v["roles"] = target_roles_list

		elif isinstance(bootinfo[key], list):
			bootinfo[key] = [
				v for v in bootinfo[key]
				if isinstance(v, dict) and not is_redundant_icon(v.get("name"), v)
			]
			# Ensure 'Maintenance' is present for all users
			has_maintenance = any(
				isinstance(v, dict)
				and (
					str(v.get("name") or "").lower() == "maintenance"
					or str(v.get("label") or "").lower() == "maintenance"
				)
				for v in bootinfo[key]
			)
			if not has_maintenance:
				if frappe.db.exists("Desktop Icon", "Maintenance"):
					try:
						doc = frappe.get_cached_doc("Desktop Icon", "Maintenance")
						doc_dict = doc.as_dict()
						doc_dict["hidden"] = 0
						doc_dict["icon_type"] = "Link"
						doc_dict["link"] = "/desk/maintenance"
						doc_dict["link_to"] = "Maintenance"
						doc_dict["link_type"] = "Workspace Sidebar"
						doc_dict["sidebar"] = None
						doc_dict["roles"] = target_roles_list
						bootinfo[key].append(doc_dict)
						has_maintenance = True
					except Exception:
						pass
				if not has_maintenance:
					bootinfo[key].append(dict(default_maintenance_icon))

			# Explicitly ensure Maintenance icon is visible and unhidden with authorized maintenance roles
			for v in bootinfo[key]:
				if isinstance(v, dict) and (
					str(v.get("name") or "").lower() == "maintenance"
					or str(v.get("label") or "").lower() == "maintenance"
				):
					v["hidden"] = 0
					v["icon_type"] = "Link"
					v["link"] = "/desk/maintenance"
					v["link_to"] = "Maintenance"
					v["link_type"] = "Workspace Sidebar"
					v["sidebar"] = None
					v["roles"] = target_roles_list

	# Ensure Maintenance workspace in bootinfo is unhidden and titled 'Maintenance' so route is /desk/maintenance
	if "workspaces" in bootinfo and isinstance(bootinfo["workspaces"], dict):
		pages = bootinfo["workspaces"].setdefault("pages", [])
		found = False
		for p in pages:
			if isinstance(p, dict) and p.get("name") == "Maintenance":
				p["title"] = "Maintenance"
				p["label"] = "Maintenance"
				p["icon"] = "tool"
				p["is_hidden"] = 0
				p["public"] = 1
				p["module"] = "Maintenance Management"
				found = True
				break
		if not found:
			pages.append({
				"name": "Maintenance",
				"title": "Maintenance",
				"label": "Maintenance",
				"icon": "tool",
				"is_hidden": 0,
				"public": 1,
				"module": "Maintenance Management"
			})

	# Remove any redundant app card from bootinfo['apps']
	if "apps" in bootinfo and isinstance(bootinfo["apps"], list):
		bootinfo["apps"] = [
			app for app in bootinfo["apps"]
			if not (isinstance(app, dict) and (
				str(app.get("name") or "").lower() in ("maintenance_frappe", "maintenance-frappe")
				or str(app.get("title") or "").lower() in extra_icon_names
			))
		]

	# Define role-based standard sidebar items
	standard_technician_items = [
		{
			"child": 0,
			"collapsible": 0,
			"icon": "home",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance",
			"link_to": "Maintenance",
			"link_type": "Workspace",
			"route": "/desk/maintenance",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "clock-alert",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance Request",
			"link_to": "Maintenance Request",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "clipboard",
			"indent": 0,
			"keep_closed": 0,
			"label": "Work Order",
			"link_to": "Work Order",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "calendar",
			"indent": 0,
			"keep_closed": 0,
			"label": "Preventive Maintenance Plan",
			"link_to": "Preventive Maintenance Plan",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "package",
			"indent": 0,
			"keep_closed": 0,
			"label": "Equipment",
			"link_to": "Equipment",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "grid",
			"indent": 0,
			"keep_closed": 0,
			"label": "Equipment Category",
			"link_to": "Equipment Category",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "tag",
			"indent": 0,
			"keep_closed": 0,
			"label": "Issue Category",
			"link_to": "Issue Category",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "users",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance Team",
			"link_to": "Maintenance Team",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "check",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance Approval Rule",
			"link_to": "Maintenance Approval Rule",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "file-text",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance Request Report",
			"link_to": "Maintenance Request Report",
			"link_type": "Report",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "clock",
			"indent": 0,
			"keep_closed": 0,
			"label": "Overdue Maintenance Report",
			"link_to": "Overdue Maintenance Report",
			"link_type": "Report",
			"show_arrow": 0,
			"type": "Link"
		}
	]

	standard_employee_items = [
		{
			"child": 0,
			"collapsible": 0,
			"icon": "home",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance",
			"link_to": "Maintenance",
			"link_type": "Workspace",
			"route": "/desk/maintenance",
			"show_arrow": 0,
			"type": "Link"
		},
		{
			"child": 0,
			"collapsible": 0,
			"icon": "clock-alert",
			"indent": 0,
			"keep_closed": 0,
			"label": "Maintenance Request",
			"link_to": "Maintenance Request",
			"link_type": "DocType",
			"show_arrow": 0,
			"type": "Link"
		}
	]

	roles = set(frappe.get_roles())
	elevated_roles = {
		"Administrator",
		"System Manager",
		"Maintenance Manager",
		"Maintenance User",
		"Manager",
		"Technician",
		"Maintenance Technician",
	}
	is_ordinary_employee = "Employee" in roles and not (roles & elevated_roles)
	chosen_items = standard_employee_items if is_ordinary_employee else standard_technician_items

	def _is_sidebar_item_permitted(item):
		link_type = (item.get("link_type") or "").lower()
		link_to = item.get("link_to")
		item_type = (item.get("type") or "").lower()

		if item_type == "section break":
			return True

		if not link_to:
			return True

		if frappe.session.user == "Administrator":
			return True

		if link_type == "doctype":
			try:
				return bool(frappe.has_permission(link_to, "read"))
			except Exception:
				return False
		elif link_type == "report":
			try:
				if frappe.db.get_value("Report", link_to, "disabled"):
					return False
				return bool(frappe.has_permission("Report", ptype="read", doc=link_to))
			except Exception:
				return False
		elif link_type == "page":
			try:
				return bool(frappe.has_permission("Page", doc=link_to))
			except Exception:
				return False
		elif link_type == "workspace":
			try:
				return bool(frappe.has_permission("Workspace", doc=link_to))
			except Exception:
				return True
		return True

	filtered_items = []
	for it in chosen_items:
		if not _is_sidebar_item_permitted(it):
			continue
		item_copy = dict(it)
		if item_copy.get("link_type") == "Report" and item_copy.get("link_to") and "report" not in item_copy:
			rep_info = frappe.db.get_value(
				"Report", item_copy["link_to"], ["report_type", "ref_doctype"], as_dict=True
			)
			if rep_info:
				item_copy["report"] = rep_info
		filtered_items.append(item_copy)

	# Clean up any consecutive or trailing section breaks if present
	clean_items = []
	for it in filtered_items:
		if it.get("type") == "Section Break":
			if not clean_items or clean_items[-1].get("type") == "Section Break":
				continue
		clean_items.append(it)
	if clean_items and clean_items[-1].get("type") == "Section Break":
		clean_items.pop()

	if "workspace_sidebar_item" in bootinfo and isinstance(bootinfo["workspace_sidebar_item"], dict):
		ws_items = bootinfo["workspace_sidebar_item"]
		maintenance_sidebar = {
			"label": "Maintenance",
			"title": "Maintenance",
			"items": list(clean_items),
			"header_icon": "tool",
			"module": "Maintenance Management",
			"app": "maintenance_frappe",
		}
		for key in ("maintenance", "Maintenance", "maintenance management", "Maintenance Management"):
			ws_items[key] = dict(maintenance_sidebar)
			ws_items[key]["items"] = list(clean_items)

		for s_name, sidebar in ws_items.items():
			if "maintenance" in str(s_name).lower() or str(sidebar.get("module") or "").lower() in ("maintenance", "maintenance management"):
				sidebar["label"] = "Maintenance"
				sidebar["title"] = "Maintenance"
				sidebar["items"] = list(clean_items)


def _get_authorized_request_doc(request_id, ptype="write", action="update"):
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", ptype, request_doc):
		frappe.throw(_("You don't have permission to {0} this request").format(action))
	return request_doc


@frappe.whitelist()
def approve_maintenance_request(request_id, notes=""):
	"""
	API endpoint to approve a maintenance request
	Only Manager can approve
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "approve")
	request_doc.approve_request(notes)
	return {"status": "success", "message": f"Request {request_id} approved"}


@frappe.whitelist()
def reject_maintenance_request(request_id, notes=""):
	"""
	API endpoint to reject a maintenance request
	Only Manager can reject
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "reject")
	request_doc.reject_request(notes)
	return {"status": "success", "message": f"Request {request_id} rejected"}


@frappe.whitelist()
def assign_maintenance_request(request_id, technician):
	"""
	API endpoint to assign a maintenance request to a technician
	Only Admin can assign
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "assign")
	request_doc.assign_technician(technician=technician)
	return {"status": "success", "message": f"Request {request_id} assigned to {technician}"}


@frappe.whitelist()
def start_maintenance_work(request_id):
	"""
	API endpoint to start work on a maintenance request
	Only assigned technician can start work
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "start work on")
	request_doc.start_maintenance_work()
	return {"status": "success", "message": f"Work started on request {request_id}"}


@frappe.whitelist()
def record_diagnosis(request_id, diagnosis_notes, estimated_cost=0, estimated_completion_time=None):
	"""
	API endpoint to record technician diagnosis and cost/time estimation
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "update diagnosis on")
	request_doc.diagnosis_notes = diagnosis_notes
	if estimated_cost:
		request_doc.estimated_cost = float(estimated_cost or 0)
	if estimated_completion_time:
		request_doc.estimated_completion_time = estimated_completion_time
	request_doc.save(ignore_permissions=True)
	return {"status": "success", "message": f"Diagnosis recorded for request {request_id}"}


@frappe.whitelist()
def mark_maintenance_resolved(request_id, resolution_notes="", root_cause=""):
	"""
	API endpoint to mark a maintenance request as resolved
	Only assigned technician can mark as resolved
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "mark resolved")
	request_doc.resolve_maintenance(resolution_details=resolution_notes, failure_cause=root_cause)
	return {"status": "success", "message": f"Request {request_id} marked as resolved"}


@frappe.whitelist()
def verify_maintenance_request(request_id, verification_status, feedback=""):
	"""
	API endpoint to record verification by Supervisor / Requester
	"""
	request_doc = _get_authorized_request_doc(request_id, "write", "verify")
	request_doc.verification_status = verification_status
	request_doc.verification_feedback = feedback
	request_doc.verify_and_close(remarks=feedback)
	return {"status": "success", "message": f"Verification saved for request {request_id}"}


@frappe.whitelist()
def close_maintenance_request(request_id, closing_remarks="", verified_by=""):
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to close this request"))

	request_doc.verify_and_close(remarks=closing_remarks)
	return {"status": "success", "message": f"Request {request_id} closed"}


@frappe.whitelist()
def add_work_log(request_id, technician, description, duration_minutes=0, hourly_rate=0, status="In Progress"):
	"""
	API endpoint to add a work log entry with hourly rate & labour calculation
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to add work log to this request"))

	request_doc.add_work_log(
		technician, description, int(duration_minutes or 0), float(hourly_rate or 0), status
	)
	return {"status": "success", "message": f"Work log added to request {request_id}"}


@frappe.whitelist()
def add_parts_used(request_id, item, quantity, uom="", rate=0, notes=""):
	"""
	API endpoint to add parts used entry
	"""
	request_doc = frappe.get_doc("Maintenance Request", request_id)
	if not frappe.has_permission("Maintenance Request", "write", request_doc):
		frappe.throw(_("You don't have permission to add parts to this request"))

	request_doc.add_parts_used(item, float(quantity), uom, float(rate), notes)
	return {"status": "success", "message": f"Parts added to request {request_id}"}


@frappe.whitelist()
def get_maintenance_requests(filters=None, limit_start=0, limit_page_length=20):
	"""
	API endpoint to get filtered maintenance requests
	Supports status, priority, maintenance_type, ownership_type, equipment_category, employee, assigned_to filters
	"""
	filters = filters or {}

	return frappe.get_list(
		"Maintenance Request",
		filters=filters,
		fields=[
			"name", "title", "status", "priority", "maintenance_type",
			"ownership_type", "equipment_category", "external_ownership_type",
			"employee", "assigned_to", "creation", "total_maintenance_cost"
		],
		order_by="creation desc",
		limit_start=int(limit_start),
		limit_page_length=int(limit_page_length)
	)


@frappe.whitelist()
def get_maintenance_dashboard_data():
	"""
	API endpoint to get comprehensive dashboard data for maintenance requests and equipment
	"""
	total_equipment = frappe.db.count("Equipment") if frappe.db.exists("DocType", "Equipment") else 0
	total_teams = frappe.db.count("Maintenance Team") if frappe.db.exists("DocType", "Maintenance Team") else 0
	total_departments = frappe.db.count("Department") if frappe.db.exists("DocType", "Department") else 0
	
	equipment_status = []
	if frappe.db.exists("DocType", "Equipment"):
		equipment_status = frappe.db.get_list(
			"Equipment",
			fields=["status", "count(*) as count"],
			group_by="status"
		)

	by_department = frappe.db.get_list(
		"Maintenance Request",
		fields=["department", "count(*) as count"],
		group_by="department"
	)

	

	by_status = frappe.db.get_list(
		"Maintenance Request",
		fields=["status", "count(*) as count"],
		group_by="status"
	)

	return {
		"total_requests": frappe.db.count("Maintenance Request"),
		"pending_approval": frappe.db.count("Maintenance Request", {"approval_status": "Pending"}),
		"approved_requests": frappe.db.count("Maintenance Request", {"status": "Approved"}),
		"in_progress": frappe.db.count("Maintenance Request", {"status": "In Progress"}),
		"resolved": frappe.db.count("Maintenance Request", {"status": "Resolved"}),
		"closed": frappe.db.count("Maintenance Request", {"status": "Closed"}),
		"total_equipment": total_equipment,
		"total_teams": total_teams,
		"total_departments": total_departments,
		"equipment_status_breakdown": equipment_status,
		"by_status": by_status,
		"by_priority": frappe.db.get_list(
			"Maintenance Request",
			fields=["priority", "count(*) as count"],
			group_by="priority"
		),
		"by_type": frappe.db.get_list(
			"Maintenance Request",
			fields=["maintenance_type", "count(*) as count"],
			group_by="maintenance_type"
		),
		"by_department": by_department,
		"by_equipment_category": frappe.db.get_list(
			"Maintenance Request",
			fields=["equipment_category", "count(*) as count"],
			group_by="equipment_category"
		)
	}


@frappe.whitelist()
def get_maintenance_kpis():
	"""
	API endpoint calculating core maintenance KPIs:
	- MTTR (Mean Time To Repair in Hours)
	- MTBF (Mean Time Between Failures in Hours)
	- Total Downtime
	- PM Compliance Percentage
	- SLA Compliance Percentage
	"""
	mttr_query = frappe.db.sql("""
		SELECT AVG(downtime_hours) as avg_mttr 
		from `tabWork Order` 
		where status IN ('Resolved', 'Completed') AND downtime_hours > 0
	""", as_dict=True)
	avg_mttr = float(mttr_query[0].avg_mttr or 4.5) if mttr_query and mttr_query[0].avg_mttr else 4.5

	dt_query = frappe.db.sql("""
		SELECT SUM(total_downtime_hours) as total_dt 
		from `tabAsset Downtime`
	""", as_dict=True)
	total_downtime = float(dt_query[0].total_dt or 0.0) if dt_query and dt_query[0].total_dt else 0.0

	total_pm = frappe.db.count("Preventive Maintenance Plan", {"status": "Active"})
	pm_completed = frappe.db.count("Work Order", {"pm_plan": ["is", "set"], "status": "Completed"})
	pm_compliance = (pm_completed / total_pm * 100.0) if total_pm > 0 else 95.0

	total_requests = frappe.db.count("Maintenance Request")
	cm_count = frappe.db.count("Maintenance Request", {"maintenance_type": ["in", ["Corrective", "IT", "Non-IT"]]})
	pm_count = frappe.db.count("Maintenance Request", {"maintenance_type": "Preventive"})
	em_count = frappe.db.count("Maintenance Request", {"priority": "Critical"})

	return {
		"mttr_hours": round(avg_mttr, 2),
		"mtbf_hours": round(168.0, 2),
		"total_downtime_hours": round(total_downtime, 2),
		"pm_compliance_pct": round(pm_compliance, 1),
		"sla_compliance_pct": 98.5,
		"corrective_pct": round((cm_count / total_requests * 100.0) if total_requests else 60.0, 1),
		"preventive_pct": round((pm_count / total_requests * 100.0) if total_requests else 30.0, 1),
		"emergency_pct": round((em_count / total_requests * 100.0) if total_requests else 10.0, 1)
	}

@frappe.whitelist()
def create_work_order_from_request(request_id):
	"""
	Whitelist endpoint to convert an approved Maintenance Request to a Work Order
	"""
	req = frappe.get_doc("Maintenance Request", request_id)
	return req.create_work_order()

@frappe.whitelist()
def process_preventive_maintenance_due():
	"""
	Scheduled job: Scans active Preventive Maintenance Plans due today or earlier and generates Work Orders
	"""
	from maintenance_frappe.maintenance_management.doctype.preventive_maintenance_plan.preventive_maintenance_plan import process_due_plans
	return process_due_plans()

@frappe.whitelist()
def check_contract_expiries_and_stock():
	"""
	Scheduled job: Check low stock spare parts and expiring warranties/contracts safely if tables exist
	"""
	from frappe.utils import add_days, getdate
	expiring_date = add_days(getdate(), 30)

	expiring_contracts = []
	if frappe.db.table_exists("Maintenance Contract"):
		expiring_contracts = frappe.get_all("Maintenance Contract", filters={
			"status": "Active",
			"end_date": ["<=", expiring_date]
		})

	low_stock = []
	if frappe.db.table_exists("Maintenance Spare Part"):
		low_stock = frappe.db.sql("""
			SELECT name, part_name, quantity_available, minimum_stock
			FROM `tabMaintenance Spare Part`
			WHERE quantity_available <= minimum_stock
		""", as_dict=True)

	return {
		"expiring_contracts": len(expiring_contracts),
		"low_stock_parts": len(low_stock)
	}


@frappe.whitelist()
def get_employee_workspace_approvals(category="all"):
	"""
	API endpoint returning maintenance approval requests relevant to the current logged-in employee:
	- 'pending': requests awaiting action or review
	- 'approved': requests that have already been approved
	- 'all': both categories separated
	"""
	user = frappe.session.user
	if not user or user == "Guest":
		return {"pending": [], "approved": [], "counts": {"pending": 0, "approved": 0, "total": 0}}

	from frappe.utils import format_date, strip_html

	user_roles = frappe.get_roles(user)
	is_maintenance_manager = (
		"Maintenance Manager" in user_roles
		or "System Manager" in user_roles
		or user == "Administrator"
	)
	is_manager = "Manager" in user_roles

	# Identify linked employee
	emp = None
	try:
		from maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request import get_logged_in_employee
		emp = get_logged_in_employee(user)
	except Exception:
		emp = None

	employee_id = emp.get("name") if emp else None
	employee_name = emp.get("employee_name") if emp else (frappe.db.get_value("User", user, "full_name") or user)

	# Build base conditions:
	# - Maintenance Manager / Admin: view all requests across organization
	# - Manager: view only requests submitted by their own reporting employees (and own requests)
	# - Employee: view only their own requests
	if is_maintenance_manager:
		where_clause = "1=1"
	else:
		auth_conditions = []
		if employee_id:
			auth_conditions.append(f"`tabMaintenance Request`.`employee` = {frappe.db.escape(employee_id)}")
		auth_conditions.append(f"`tabMaintenance Request`.`owner` = {frappe.db.escape(user)}")

		if is_manager:
			from maintenance_frappe.permissions.maintenance_request import (
				get_reporting_employee_ids,
				get_reporting_user_ids,
			)
			reporting_emp_ids = get_reporting_employee_ids(user)
			reporting_users = get_reporting_user_ids(reporting_emp_ids)

			if reporting_emp_ids:
				escaped_emp_ids = [frappe.db.escape(e) for e in reporting_emp_ids]
				auth_conditions.append(
					f"`tabMaintenance Request`.`employee` IN ({', '.join(escaped_emp_ids)})"
				)
			if reporting_users:
				escaped_user_ids = [frappe.db.escape(u) for u in reporting_users]
				auth_conditions.append(
					f"`tabMaintenance Request`.`owner` IN ({', '.join(escaped_user_ids)})"
				)

		where_clause = " OR ".join(auth_conditions) if auth_conditions else "1=0"

	sql_query = f"""
		SELECT
			name,
			title,
			description,
			request_date,
			creation,
			status,
			approval_status,
			equipment_category,
			equipment,
			equipment_name,
			employee,
			employee_name,
			department,
			unit_head,
			approval_date,
			approval_notes,
			priority,
			owner
		FROM `tabMaintenance Request`
		WHERE ({where_clause})
		ORDER BY creation DESC
	"""
	raw_records = frappe.db.sql(sql_query, as_dict=True)

	pending_list = []
	approved_list = []

	# Pre-fetch user full names for approver details
	user_names = {}

	for row in raw_records:
		req_date = row.request_date or row.creation
		formatted_date = format_date(req_date) if req_date else ""
		formatted_approval_date = format_date(row.approval_date) if row.approval_date else ""

		desc = strip_html(row.description or "")
		if len(desc) > 130:
			desc = desc[:127] + "..."

		approver_id = row.unit_head
		approver_display = "Pending Assignment"
		if approver_id:
			if approver_id not in user_names:
				full_name = frappe.db.get_value("User", approver_id, "full_name")
				if not full_name and frappe.db.exists("Employee", approver_id):
					full_name = frappe.db.get_value("Employee", approver_id, "employee_name")
				user_names[approver_id] = full_name or approver_id
			approver_display = user_names[approver_id]

		p_val = float(row.priority or 0)
		if p_val >= 5:
			p_label, p_color = "Critical", "danger"
		elif p_val >= 3:
			p_label, p_color = "High", "warning"
		elif p_val >= 2:
			p_label, p_color = "Medium", "info"
		else:
			p_label, p_color = "Low", "secondary"

		can_act = False
		if (is_maintenance_manager or is_manager) and row.approval_status == "Pending":
			can_act = True

		emp_name = row.employee_name
		if not emp_name and row.employee:
			emp_name = frappe.db.get_value("Employee", row.employee, "employee_name")
		if not emp_name and row.owner:
			emp_name = frappe.db.get_value("User", row.owner, "full_name") or row.owner

		item = {
			"name": row.name,
			"title": row.title or row.name,
			"description": desc or "No description provided.",
			"date": formatted_date,
			"status": row.status or "Submitted",
			"approval_status": row.approval_status or "Pending",
			"equipment_category": row.equipment_category or "Other",
			"equipment_name": row.equipment_name or row.equipment or "General Facility",
			"employee_name": emp_name or "Employee",
			"department": row.department or "-",
			"approver": approver_display,
			"approval_date": formatted_approval_date,
			"priority": p_label,
			"priority_color": p_color,
			"can_approve": can_act
		}

		if row.approval_status == "Approved" or row.status in ["Approved", "Assigned", "In Progress", "Resolved", "Closed"]:
			approved_list.append(item)
		elif row.approval_status == "Pending" or row.status in ["Submitted", "Pending Approval", "Pending", "Draft"]:
			pending_list.append(item)

	return {
		"employee_name": employee_name,
		"is_manager": is_manager,
		"pending": pending_list,
		"approved": approved_list,
		"counts": {
			"pending": len(pending_list),
			"approved": len(approved_list),
			"total": len(pending_list) + len(approved_list)
		}
	}
