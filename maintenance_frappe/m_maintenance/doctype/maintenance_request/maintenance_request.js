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
			let filters = {
				'status': ['not in', ['Retired', 'Disposed']]
			};
			if (frm.doc.equipment_category) {
				filters['equipment_category'] = frm.doc.equipment_category;
			}
			if (frm.doc.maintenance_type) {
				filters['maintenance_type'] = frm.doc.maintenance_type;
			}
			if (frm.doc.department) {
				filters['department'] = frm.doc.department;
			}
			return { filters: filters };
		});

		frm.set_query('issue_category', function() {
			return {
				query: 'maintenance_frappe.m_maintenance.doctype.issue_category.issue_category.get_issue_categories',
				filters: {
					is_active: 1,
					equipment_category: frm.doc.equipment_category || ''
				}
			};
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

	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.db.get_doc('Employee', frm.doc.employee).then(emp => {
				if (emp) {
					if (emp.employee_name) frm.set_value('employee_name', emp.employee_name);
					if (emp.department && !frm.doc.department) frm.set_value('department', emp.department);
					if (emp.company && !frm.doc.company) frm.set_value('company', emp.company);
					if (emp.unit && !frm.doc.unit) frm.set_value('unit', emp.unit);
				}
			});
		}
	},

	ownership_type: function(frm) {
		frm.trigger('setup_queries');
	},

	maintenance_type: function(frm) {
		frm.trigger('setup_queries');
	},

	equipment_category: function(frm) {
		if (frm.doc.issue_category) {
			frappe.db.get_value('Issue Category', frm.doc.issue_category, 'equipment_category').then(r => {
				if (r && r.message && r.message.equipment_category && r.message.equipment_category !== frm.doc.equipment_category) {
					frm.set_value('issue_category', null);
				}
			});
		}
		if (frm.doc.equipment) {
			frappe.db.get_value('Equipment', frm.doc.equipment, 'equipment_category').then(r => {
				if (r && r.message && r.message.equipment_category && r.message.equipment_category !== frm.doc.equipment_category) {
					frm.set_value('equipment', null);
				}
			});
		}
		frm.trigger('setup_queries');
		frm.trigger('update_maintenance_type_options');
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
					if (!frm.doc.equipment_category && eq.equipment_category) {
						frm.set_value('equipment_category', eq.equipment_category);
					}
					if (!frm.doc.maintenance_type && eq.maintenance_type) {
						frm.set_value('maintenance_type', eq.maintenance_type);
					}
					if (eq.department && !frm.doc.department) {
						frm.set_value('department', eq.department);
					}
					if (eq.unit && !frm.doc.unit) {
						frm.set_value('unit', eq.unit);
					}
					if (eq.asset_id && !frm.doc.asset) {
						frm.set_value('asset', eq.asset_id);
					}
				}
			});
		}
	},

	set_section_visibilities: function(frm) {
		let user_roles = frappe.user_roles || [];
		let is_admin_or_approver = user_roles.includes('System Manager') || 
			user_roles.includes('Maintenance Manager') || 
			user_roles.includes('Maintenance User') || 
			user_roles.includes('Unit Head') || 
			user_roles.includes('Supervisor') || 
			user_roles.includes('Technician');

		let hide_approval_and_below = !is_admin_or_approver;

		frm.set_df_property('section_approval_assignment', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_diagnosis', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_work_details', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_resolution', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_verification', 'hidden', hide_approval_and_below ? 1 : 0);
		frm.set_df_property('section_closure', 'hidden', hide_approval_and_below ? 1 : 0);
	},

	set_field_states: function(frm) {
		if (frm.doc.approval_status === 'Rejected' || frm.doc.status === 'Rejected' || frm.doc.status === 'Closed') {
			frm.disable_save();
		}
	},

	setup_workflow_buttons: function(frm) {
		if (frm.is_new()) return;

		// 1. Pending Approval Actions
		if (frm.doc.status === 'Pending Approval') {
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
						args: { remarks: values.remarks },
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
						args: { remarks: values.remarks },
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

		// 2. Approved / Planning -> Assign
		if (frm.doc.status === 'Approved' || frm.doc.status === 'Planned') {
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
						label: __('Responsible Person / Technician'),
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

			frm.add_custom_button(__('Create Work Order'), function() {
				frappe.call({
					doc: frm.doc,
					method: 'create_work_order',
					callback: function(r) {
						if (!r.exc && r.message) {
							frappe.show_alert({ message: __('Work Order Created: ') + r.message, indicator: 'green' });
							frm.reload_doc();
						}
					}
				});
			}, __('Actions'));
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

		// 4. In Progress -> Resolve / On Hold
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
						default: frm.doc.diagnosis_notes || ''
					},
					{
						fieldname: 'work_details',
						fieldtype: 'Small Text',
						label: __('Work Details'),
						reqd: 1,
						default: frm.doc.work_performed || ''
					},
					{
						fieldname: 'resolution_details',
						fieldtype: 'Small Text',
						label: __('Resolution Details'),
						reqd: 1,
						default: frm.doc.resolution_notes || ''
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

			frm.add_custom_button(__('Put On Hold'), function() {
				frappe.prompt([
					{
						fieldname: 'reason',
						fieldtype: 'Select',
						options: ['Parts Unavailable', 'Vendor Delay', 'Other'],
						label: __('Hold Reason'),
						reqd: 1
					}
				], function(values) {
					frappe.call({
						doc: frm.doc,
						method: 'put_on_hold',
						args: { reason: values.reason },
						callback: function(r) {
							if (!r.exc) {
								frappe.show_alert({ message: __('Work Put On Hold'), indicator: 'orange' });
								frm.reload_doc();
							}
						}
					});
				}, __('Put Maintenance Work On Hold'), __('Put On Hold'));
			}, __('Actions'));
		}

		// 5. On Hold -> Resume Work
		if (frm.doc.status === 'On Hold') {
			frm.add_custom_button(__('Resume Work'), function() {
				frappe.call({
					doc: frm.doc,
					method: 'resume_work',
					callback: function(r) {
						if (!r.exc) {
							frappe.show_alert({ message: __('Work Resumed'), indicator: 'green' });
							frm.reload_doc();
						}
					}
				});
			}, __('Actions')).addClass('btn-primary');
		}

		// 6. Resolved -> Verification & Close / Rework
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

