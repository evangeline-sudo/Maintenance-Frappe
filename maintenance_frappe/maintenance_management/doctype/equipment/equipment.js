// Copyright (c) 2026, Evangeline and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment', {
	setup: function(frm) {
		frm.set_query('equipment_category', function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		if (frm.fields_dict.location) {
			frm.set_query('location', function() {
				return {
					filters: {
						is_active: 1
					}
				};
			});
		}
	}
});
