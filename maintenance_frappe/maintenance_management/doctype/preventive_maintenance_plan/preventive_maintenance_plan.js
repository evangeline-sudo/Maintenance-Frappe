frappe.ui.form.on('Preventive Maintenance Plan', {
	refresh: function(frm) {
		if (!frm.is_new() && frm.doc.status === 'Active') {
			frm.add_custom_button(__('Generate Work Order'), function() {
				frappe.call({
					doc: frm.doc,
					method: 'generate_work_order',
					callback: function(r) {
						if (!r.exc && r.message) {
							frappe.show_alert({
								message: __('Work Order created: ') + r.message,
								indicator: 'green'
							});
							frm.reload_doc();
						}
					}
				});
			}, __('Actions')).addClass('btn-primary');
		}
	},

	equipment: function(frm) {
		if (frm.doc.equipment) {
			frappe.db.get_doc('Equipment', frm.doc.equipment).then(eq => {
				if (eq) {
					if (eq.equipment_name) {
						frm.set_value('equipment_name', eq.equipment_name);
					}
					if (eq.equipment_category) {
						frm.set_value('equipment_category', eq.equipment_category);
					}
					if (eq.maintenance_team && !frm.doc.assigned_team) {
						frm.set_value('assigned_team', eq.maintenance_team);
					}
				}
			});
		}
	}
});
