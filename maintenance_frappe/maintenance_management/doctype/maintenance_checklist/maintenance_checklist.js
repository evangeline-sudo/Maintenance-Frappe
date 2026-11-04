// Copyright (c) 2026, Evangeline and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Checklist', {
	setup: function(frm) {
		frm.set_query('equipment_category', function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});
	}
});

