frappe.query_reports["Overdue Maintenance Report"] = {
	"filters": [
		{
			"fieldname": "equipment_category",
			"label": __("Equipment Category"),
			"fieldtype": "Select",
			"options": "\nIT Equipment\nElectrical Equipment\nVehicle\nMachine\nFurniture\nBuilding/Facility\nMedical Equipment\nOffice Equipment\nOther"
		},
		{
			"fieldname": "priority",
			"label": __("Priority"),
			"fieldtype": "Select",
			"options": "\nLow\nMedium\nHigh\nCritical"
		}
	]
};
