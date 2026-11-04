frappe.ui.form.on('Work Order', {
	refresh: function(frm) {
		frm.trigger('show_linked_request_employee');

		if (frm.is_new()) return;

		// 1. Scheduled / Open -> Start Work
		if (frm.doc.status === 'Scheduled' || frm.doc.status === 'Draft') {
			frm.add_custom_button(__('Start Work'), function() {
				frm.set_value('status', 'In Progress');
				if (!frm.doc.actual_start) {
					frm.set_value('actual_start', frappe.datetime.now_datetime());
				}
				frm.save();
			}, __('Actions')).addClass('btn-primary');
		}

		// 2. In Progress -> Complete Work / On Hold
		if (frm.doc.status === 'In Progress') {
			frm.add_custom_button(__('Complete Work'), function() {
				frappe.prompt([
					{
						fieldname: 'work_performed',
						fieldtype: 'Small Text',
						label: __('Work Performed'),
						reqd: 1,
						default: frm.doc.work_performed || ''
					},
					{
						fieldname: 'resolution',
						fieldtype: 'Small Text',
						label: __('Resolution Details'),
						default: frm.doc.resolution || ''
					}
				], function(values) {
					frm.set_value('status', 'Completed');
					frm.set_value('actual_end', frappe.datetime.now_datetime());
					frm.set_value('work_performed', values.work_performed);
					if (values.resolution) {
						frm.set_value('resolution', values.resolution);
					}
					frm.save();
				}, __('Complete Work Order'), __('Complete'));
			}, __('Actions')).addClass('btn-primary');

			frm.add_custom_button(__('Put On Hold'), function() {
				frm.set_value('status', 'On Hold');
				frm.save();
			}, __('Actions'));
		}

		// 3. On Hold -> Resume Work
		if (frm.doc.status === 'On Hold') {
			frm.add_custom_button(__('Resume Work'), function() {
				frm.set_value('status', 'In Progress');
				frm.save();
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
					let loc = eq.used_in_location || eq.location;
					if (loc) {
						frm.set_value('location', loc);
					}
					if (eq.department && !frm.doc.department) {
						frm.set_value('department', eq.department);
					}
					if (eq.maintenance_team && !frm.doc.assigned_team) {
						frm.set_value('assigned_team', eq.maintenance_team);
					}
				}
			});
		}
	},

	maintenance_request: function(frm) {
		frm.trigger('show_linked_request_employee');
	},

	show_linked_request_employee: function(frm) {
		if (frm.doc.maintenance_request) {
			frappe.db.get_value('Maintenance Request', frm.doc.maintenance_request, ['employee', 'employee_name']).then(r => {
				if (r && r.message) {
					const emp = r.message.employee || '';
					const emp_name = r.message.employee_name || '';
					const display = emp_name ? (emp ? `${emp_name} (${emp})` : emp_name) : emp;
					if (display) {
						frm.set_df_property('maintenance_request', 'description', __('Employee: <b>{0}</b>', [display]));
					} else {
						frm.set_df_property('maintenance_request', 'description', '');
					}
				} else {
					frm.set_df_property('maintenance_request', 'description', '');
				}
			});
		} else {
			frm.set_df_property('maintenance_request', 'description', '');
		}
	}
});
