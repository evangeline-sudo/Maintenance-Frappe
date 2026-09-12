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

		frm.set_query('product_type', function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});

		frm.set_query('location', function() {
			return {
				filters: {
					is_active: 1
				}
			};
		});
	}
});

