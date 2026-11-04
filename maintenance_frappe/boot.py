# Copyright (c) 2026, Evangeline and contributors
# For license information, please see license.txt

import frappe
from frappe.desk.desktop import Workspace


def boot_session(bootinfo):
	"""Ensure Maintenance workspace is accessible in user bootinfo without module restrictions."""
	if not frappe.session.user or frappe.session.user == "Guest":
		return

	# Prevent Maintenance Management from being erroneously blocked in Block Module
	try:
		if frappe.db.exists("Block Module", {"parent": frappe.session.user, "module": "Maintenance Management"}):
			frappe.db.delete("Block Module", {"parent": frappe.session.user, "module": "Maintenance Management"})
			frappe.db.commit()
	except Exception:
		pass

	# Ensure Maintenance workspace is present in bootinfo.workspaces.pages
	if bootinfo.get("workspaces") and isinstance(bootinfo.workspaces, dict):
		pages = bootinfo.workspaces.get("pages", [])
		if not any(p.get("name") == "Maintenance" for p in pages):
			try:
				ws_doc = frappe.get_cached_doc("Workspace", "Maintenance")
				ws = Workspace(ws_doc.as_dict(), True)
				if ws.is_permitted():
					page_dict = ws_doc.as_dict()
					page_dict["label"] = frappe._(page_dict.get("name"))
					pages.append(page_dict)
					bootinfo.workspaces["pages"] = pages
			except Exception:
				pass

