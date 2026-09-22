import frappe
from frappe.model.document import Document


class IssueCategory(Document):
	pass


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_issue_categories(doctype, txt, searchfield, start, page_len, filters):
	filters = filters or {}
	eq_cat = filters.get("equipment_category")

	conditions = ["is_active = 1"]
	values = {}

	if eq_cat:
		conditions.append("(equipment_category = %(eq_cat)s OR equipment_category IS NULL OR equipment_category = '')")
		values["eq_cat"] = eq_cat

	if txt:
		conditions.append("(name LIKE %(txt)s OR issue_category_name LIKE %(txt)s)")
		values["txt"] = f"%{txt}%"

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT name, issue_category_name, equipment_category
		FROM `tabIssue Category`
		WHERE {where_clause}
		ORDER BY name ASC
		LIMIT %(start)s, %(page_len)s
		""",
		{**values, "start": start, "page_len": page_len},
	)


