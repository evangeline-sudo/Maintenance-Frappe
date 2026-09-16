const CATEGORY_MAINTENANCE_TYPE_MAP = {
	'IT Equipment': ['IT'],
	'Electrical Equipment': ['Non-IT'],
	'Vehicle': ['Non-IT'],
	'Machine': ['Non-IT'],
	'Furniture': ['Non-IT'],
	'Building/Facility': ['Non-IT'],
	'Office Equipment': ['Non-IT'],
	'Medical Equipment': ['Professional-Specialized'],
	'Other': ['Non-IT']
};

frappe.ui.form.on('Maintenance Request', {
	setup: function(frm) {
		frm.trigger('setup_queries');
	},

	setup_queries: function(frm) {
		frm.set_query('equipment', function() {
			return {
				query: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_equipment_for_category',
				filters: {
					equipment_category: frm.doc.equipment_category || ''
				}
			};
		});

		frm.set_query('unit_head', function() {
			return {
				query: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_manager_users'
			};
		});

		frm.set_query('issue_category', function() {
			let filters = { is_active: 1 };
			if (frm.doc.equipment_category) {
				filters['equipment_category'] = frm.doc.equipment_category;
			}
			return { filters: filters };
		});

		frm.set_query('location', function() {
			return { filters: { is_active: 1 } };
		});

		frm.set_query('assigned_team', function() {
			return { filters: { is_active: 1 } };
		});

		frm.set_query('responsible_person', function() {
			let filters = { is_active: 1 };
			if (frm.doc.assigned_team) {
				filters['maintenance_team'] = frm.doc.assigned_team;
			}
			return { filters: filters };
		});
	},

	refresh: function(frm) {
		frm.trigger('setup_queries');
		frm.trigger('update_maintenance_type_options');
		frm.trigger('setup_workflow_buttons');
		frm.trigger('set_field_states');
		frm.trigger('set_section_visibilities');
	},

	onload: function(frm) {
		frm.trigger('update_maintenance_type_options');
		frm.trigger('set_section_visibilities');
	},

	ownership_type: function(frm) {
		frm.trigger('setup_queries');
	},

	maintenance_type: function(frm) {
		frm.trigger('setup_queries');
	},

	equipment_category: function(frm) {
		frm.trigger('setup_queries');
		frm.trigger('update_maintenance_type_options');

		// Check if current equipment matches the new category; if not, clear it
		if (frm.doc.equipment && frm.doc.equipment_category) {
			frappe.call({
				method: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_matching_equipment_categories',
				args: {
					equipment_category: frm.doc.equipment_category
				},
				callback: function(r) {
					let matching_cats = r.message || [];
					frappe.db.get_value('Equipment', frm.doc.equipment, 'equipment_category').then(val => {
						let current_eq_cat = val && val.message ? val.message.equipment_category : null;
						if (current_eq_cat && !matching_cats.includes(current_eq_cat)) {
							frm.set_value('equipment', '');
							frm.set_value('equipment_name', '');
							frm.set_value('equipment_serial', '');
							frm.set_value('equipment_location', '');
						}
					});
				}
			});
		}
	},

	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.call({
				method: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_employee_manager_user',
				args: {
					employee: frm.doc.employee
				},
				callback: function(r) {
					if (r.message) {
						if (r.message.employee_name && !frm.doc.employee_name) {
							frm.set_value('employee_name', r.message.employee_name);
						}
						if (r.message.user_id) {
							frm.set_value('unit_head', r.message.user_id);
						}
						frm.trigger('set_field_states');
					}
				}
			});
		} else {
			frm.set_value('employee_name', '');
		}
	},

	unit_head: function(frm) {
		frm.trigger('set_field_states');
		frm.trigger('set_section_visibilities');
	},

	update_maintenance_type_options: function(frm) {
		if (frm.doc.equipment_category) {
			let allowed_types = CATEGORY_MAINTENANCE_TYPE_MAP[frm.doc.equipment_category] || ['Non-IT'];
			frm.set_df_property('maintenance_type', 'options', allowed_types);
			if (!frm.doc.maintenance_type || !allowed_types.includes(frm.doc.maintenance_type)) {
				frm.set_value('maintenance_type', allowed_types[0]);
			}
		} else {
			frm.set_df_property('maintenance_type', 'options', ['IT', 'Non-IT', 'Professional-Specialized']);
		}
	},

	department: function(frm) {
		frm.trigger('setup_queries');
	},

	equipment: function(frm) {
		if (frm.doc.equipment) {
			frappe.db.get_doc('Equipment', frm.doc.equipment).then(eq => {
				if (eq) {
					if (eq.equipment_name) {
						frm.set_value('equipment_name', eq.equipment_name);
					}
					if (eq.serial_number || eq.equipment_id) {
						frm.set_value('equipment_serial', eq.serial_number || eq.equipment_id);
					}
					if (eq.location) {
						frm.set_value('equipment_location', eq.location);
						if (!frm.doc.location) {
							frm.set_value('location', eq.location);
						}
					}
					if (eq.asset_id && !frm.doc.asset) {
						frm.set_value('asset', eq.asset_id);
					}
					if (!frm.doc.equipment_category && eq.equipment_category) {
						frm.set_value('equipment_category', eq.equipment_category);
					}
					if (!frm.doc.maintenance_type && eq.maintenance_type) {
						frm.set_value('maintenance_type', eq.maintenance_type);
					}
				}
			});
		} else {
			frm.set_value('equipment_name', '');
			frm.set_value('equipment_serial', '');
			frm.set_value('equipment_location', '');
		}
	},

	set_section_visibilities: function(frm) {
		let user_roles = frappe.user_roles || [];
		let is_admin_or_approver = (
			frappe.session.user === 'Administrator' ||
			user_roles.includes('System Manager') || 
			user_roles.includes('Maintenance Manager') ||
			user_roles.includes('Maintenance User') || 
			user_roles.includes('Unit Head') || 
			user_roles.includes('Supervisor') || 
			user_roles.includes('Technician') ||
			(frm.doc.unit_head && frappe.session.user === frm.doc.unit_head)
		);

		// Hide Approval & Assignment and all subsequent sections for standard Employee role unless they are the unit head
		let hide_approval_and_below = !is_admin_or_approver;

		frm.set_df_property('section_approval_assignment', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_diagnosis', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_work_details', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_resolution', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_verification', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_closure', 'hidden', hide_approval_and_below ? 1 : 0);
	},

	set_field_states: function(frm) {
		let user_roles = frappe.user_roles || [];
		let is_authorized_approver = (
			frappe.session.user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Maintenance Manager') ||
			(frm.doc.unit_head && frappe.session.user === frm.doc.unit_head)
		);

		// Approval Status can only be changed by Maintenance Manager, System Manager, Admin, or assigned Unit Head User
		frm.set_df_property('approval_status', 'read_only', is_authorized_approver ? 0 : 1);

		if (frm.doc.approval_status === 'Rejected') {
			frm.disable_save();
		}
	},

	setup_workflow_buttons: function(frm) {
		if (frm.is_new()) return;

		let user_roles = frappe.user_roles || [];
		let can_approve = (
			frappe.session.user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Maintenance Manager') ||
			(frm.doc.unit_head && frappe.session.user === frm.doc.unit_head)
		);

		// 1. Pending / Hold Approval Actions - only for Maintenance Manager, System Manager, Admin, or assigned Unit Head
		if ((frm.doc.approval_status === 'Pending' || frm.doc.approval_status === 'Hold' || frm.doc.status === 'Pending Approval') && can_approve) {
			frm.add_custom_button(__('Approve'), function() {
				frappe.prompt([
					{
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						label: __('Approval Remarks')
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'approve_request',
						args: { approval_notes: values.remarks },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Request Approved'), indicator: 'green' });
								frm.reload_doc();
							}
						}
					});
				}, __('Approve Maintenance Request'), __('Approve'));
			}, __('Actions')).addClass('btn-primary');

				frm.add_custom_button(__('Reject'), function() {
					frappe.prompt([
						{
							fieldname: 'remarks',
							fieldtype: 'Small Text',
							label: __('Rejection Reason'),
							reqd: 1
						}
					], function(values) {
						frappe.call({
							doc: frm.doc,
							method: 'reject_request',
							args: { approval_notes: values.remarks },
							callback: function(r) {
								if (!r.exc) {
									frappe.show_alert({ message: __('Request Rejected'), indicator: 'red' });
									frm.reload_doc();
								}
							}
						});
					}, __('Reject Maintenance Request'), __('Reject'));
				}, __('Actions')).addClass('btn-danger');
		}

		// 2. Approved -> Assign
		if ((frm.doc.approval_status === 'Approved' || frm.doc.status === 'Approved') && !frm.doc.assigned_to) {
			frm.add_custom_button(__('Assign Technician'), function() {
				frappe.prompt([
					{
						fieldname: 'assigned_team',
						fieldtype: 'Link',
						options: 'Maintenance Team',
						label: __('Maintenance Team'),
						reqd: 1
					},
					{
						fieldname: 'responsible_person',
						fieldtype: 'Link',
						options: 'Responsible Person',
						label: __('Responsible Person'),
						reqd: 1
					},
					{
						fieldname: 'expected_completion_date',
						fieldtype: 'Date',
						label: __('Expected Completion Date')
					},
					{
						fieldname: 'assignment_remarks',
						fieldtype: 'Small Text',
						label: __('Assignment Remarks')
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'assign_technician',
						args: {
							team: values.assigned_team,
							technician: values.responsible_person,
							expected_date: values.expected_completion_date,
							remarks: values.assignment_remarks
						},
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Technician Assigned'), indicator: 'green' });
								frm.reload_doc();
							}
						}
					});
				}, __('Assign Maintenance Team & Technician'), __('Assign'));
			}, __('Actions')).addClass('btn-primary');
		}

		// 3. Assigned -> Start Work
		if (frm.doc.status === 'Assigned') {
			frm.add_custom_button(__('Start Work'), function() {
				frappe.call({
					doc: frm.doc,
					method: 'start_maintenance_work',
					callback: function(r) {
						if (!r.exc) {
							frappe.show_alert({ message: __('Maintenance Work Started'), indicator: 'green' });
							frm.reload_doc();
						}
					}
				});
			}, __('Actions')).addClass('btn-primary');
		}

		// 4. In Progress -> Resolve
		if (frm.doc.status === 'In Progress') {
			frm.add_custom_button(__('Resolve Request'), function() {
				frappe.prompt([
					{
						fieldname: 'resolution_type',
						fieldtype: 'Link',
						options: 'Maintenance Resolution Type',
						label: __('Resolution Type'),
						reqd: 1
					},
					{
						fieldname: 'diagnosis',
						fieldtype: 'Small Text',
						label: __('Diagnosis'),
						reqd: 1,
						default: frm.doc.diagnosis || ''
					},
					{
						fieldname: 'work_details',
						fieldtype: 'Small Text',
						label: __('Work Details'),
						reqd: 1,
						default: frm.doc.work_details || ''
					},
					{
						fieldname: 'resolution_details',
						fieldtype: 'Small Text',
						label: __('Resolution Details'),
						reqd: 1,
						default: frm.doc.resolution_details || ''
					},
					{
						fieldname: 'failure_cause',
						fieldtype: 'Link',
						options: 'Maintenance Cause',
						label: __('Failure Cause')
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'resolve_maintenance',
						args: {
							resolution_type: values.resolution_type,
							resolution_details: values.resolution_details,
							diagnosis: values.diagnosis,
							work_details: values.work_details,
							failure_cause: values.failure_cause
						},
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Request Marked Resolved'), indicator: 'green' });
								frm.reload_doc();
							}
						}
					});
				}, __('Resolve Maintenance Request'), __('Mark Resolved'));
			}, __('Actions')).addClass('btn-primary');
		}

		// 5. Resolved -> Verification & Close / Rework
		if (frm.doc.status === 'Resolved') {
			frm.add_custom_button(__('Verify & Close'), function() {
				frappe.prompt([
					{
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						label: __('Verification Remarks')
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'verify_and_close',
						args: { remarks: values.remarks },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Request Verified and Closed'), indicator: 'green' });
								frm.reload_doc();
							}
						}
					});
				}, __('Verify & Close Maintenance Request'), __('Accept & Close'));
			}, __('Actions')).addClass('btn-primary');

			frm.add_custom_button(__('Request Rework'), function() {
				frappe.prompt([
					{
						fieldname: 'remarks',
						fieldtype: 'Small Text',
						label: __('Rework Reason & Instructions'),
						reqd: 1
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'request_rework',
						args: { remarks: values.remarks },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Returned for Rework'), indicator: 'orange' });
								frm.reload_doc();
							}
						}
					});
				}, __('Request Maintenance Rework'), __('Submit Rework'));
			}, __('Actions')).addClass('btn-warning');
		}
	}
});

