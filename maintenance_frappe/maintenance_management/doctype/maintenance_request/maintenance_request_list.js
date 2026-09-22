frappe.listview_settings['Maintenance Request'] = {
	get_indicator: function(doc) {
		if (doc.status === "Submitted") {
			return [__("Submitted"), "blue", "status,=,Submitted"];
		} else if (doc.status === "Pending Approval") {
			return [__("Pending Approval"), "orange", "status,=,Pending Approval"];
		} else if (doc.status === "Approved") {
			return [__("Approved"), "green", "status,=,Approved"];
		} else if (doc.status === "Assigned") {
			return [__("Assigned"), "cyan", "status,=,Assigned"];
		} else if (doc.status === "In Progress") {
			return [__("In Progress"), "purple", "status,=,In Progress"];
		} else if (doc.status === "On Hold") {
			return [__("On Hold"), "yellow", "status,=,On Hold"];
		} else if (doc.status === "Resolved") {
			return [__("Resolved"), "green", "status,=,Resolved"];
		} else if (doc.status === "Rejected") {
			return [__("Rejected"), "red", "status,=,Rejected"];
		} else if (doc.status === "Closed") {
			return [__("Closed"), "gray", "status,=,Closed"];
		}
	}
};

