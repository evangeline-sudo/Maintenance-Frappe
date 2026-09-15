frappe.query_reports["Total Equipment Report"] = {
	"filters": [
		{
			"fieldname": "equipment_category",
			"label": __("Equipment Category"),
			"fieldtype": "Link",
			"options": "Equipment Category"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nUnder Maintenance\nRetired\nDisposed"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		}
	]
};
