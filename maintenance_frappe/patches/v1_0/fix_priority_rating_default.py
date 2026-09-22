import frappe

def execute():
	"""
	Pre-sync patch: Fix invalid string defaults ('Medium', 'Low', 'High', 'Critical')
	for the numeric Rating column 'priority' on Maintenance Request, Work Order,
	and Maintenance Approval Rule to prevent MySQLdb.OperationalError (1292 / 1067).
	"""
	try:
		frappe.db.sql("SET SESSION sql_mode = ''")
	except Exception:
		pass

	for doctype in ["Maintenance Request", "Work Order", "Maintenance Approval Rule"]:
		try:
			table_name = f"tab{doctype}"

			# 1. Clear invalid string defaults from tabDocField for priority rating field
			frappe.db.sql("""
				UPDATE `tabDocField`
				SET `default` = NULL
				WHERE `parent` = %s AND `fieldname` = 'priority' AND `default` IS NOT NULL
			""", doctype)

			# 2. Clear default from tabCustom Field if present
			if frappe.db.table_exists("Custom Field"):
				frappe.db.sql("""
					UPDATE `tabCustom Field`
					SET `default` = NULL
					WHERE `dt` = %s AND `fieldname` = 'priority' AND `default` IS NOT NULL
				""", doctype)

			# 3. Clean up data and convert column in MariaDB if table exists
			if frappe.db.table_exists(doctype):
				if frappe.db.has_column(doctype, "priority"):
					frappe.db.sql(f"ALTER TABLE `{table_name}` ALTER COLUMN `priority` DROP DEFAULT", ignore_err=True)
					frappe.db.sql(f"""
						UPDATE `{table_name}`
						SET `priority` = CASE
							WHEN CAST(`priority` AS CHAR) LIKE '%%Low%%' THEN '1.0'
							WHEN CAST(`priority` AS CHAR) LIKE '%%Med%%' THEN '2.0'
							WHEN CAST(`priority` AS CHAR) LIKE '%%High%%' THEN '3.0'
							WHEN CAST(`priority` AS CHAR) LIKE '%%Crit%%' THEN '5.0'
							WHEN CAST(`priority` AS CHAR) NOT REGEXP '^[0-9]+(\\\\.[0-9]+)?$' OR `priority` IS NULL OR `priority` = '' THEN '2.0'
							ELSE `priority`
						END
					""")
					frappe.db.sql(f"ALTER TABLE `{table_name}` MODIFY `priority` decimal(3,2) DEFAULT 0.00", ignore_err=True)
		except Exception as e:
			frappe.log_error(f"Error fixing priority rating default for {doctype}: {e}")

	# Ensure production_item, bom_no, and manufacturing fields are not required for Work Order
	clear_work_order_mandatory_fields()

	# Ensure Page and Workspace read permissions for standard maintenance roles
	ensure_page_permissions()

	frappe.db.commit()


def clear_work_order_mandatory_fields():
	"""Clear mandatory reqd = 1 flags on ERPNext manufacturing fields for Work Order."""
	try:
		frappe.db.sql("""
			UPDATE `tabDocField`
			SET reqd = 0
			WHERE parent = 'Work Order' AND fieldname IN ('production_item', 'bom_no', 'qty', 'fg_completed_qty', 'wip_warehouse', 'fg_warehouse')
		""")
		if frappe.db.table_exists("Custom Field"):
			frappe.db.sql("""
				UPDATE `tabCustom Field`
				SET reqd = 0
				WHERE dt = 'Work Order' AND fieldname IN ('production_item', 'bom_no', 'qty', 'fg_completed_qty', 'wip_warehouse', 'fg_warehouse')
			""")
	except Exception as e:
		frappe.log_error(f"Error clearing Work Order mandatory fields: {e}")


def ensure_page_permissions():
	"""Ensure Employee, Manager, Maintenance Manager, Technician, and All roles have Read access to Page and Workspace across DocPerm and Custom DocPerm."""
	target_roles = ["All", "Employee", "Manager", "Maintenance Manager", "Technician", "System Manager"]
	for doctype in ["Page", "Workspace"]:
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

		# 2. Custom DocPerm (if custom permissions exist for Page/Workspace)
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
