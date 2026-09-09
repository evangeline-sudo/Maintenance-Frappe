// Copyright (c) 2026, Evangeline and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Request', {
	setup: function(frm) {
		frm.set_query('equipment', function() {
			return {
				filters: [
					['Equipment', 'status', 'not in', ['Retired', 'Disposed']]
				]
			};
		});

		frm.set_query('issue_category', function() {
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

		frm.set_query('assigned_team', function() {
			return {
				filters: {
					is_active: 1
				}
			};
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
		frm.trigger('setup_workflow_buttons');
		frm.trigger('set_field_states');
	},

	assigned_team: function(frm) {
		// Clear responsible person if not in team
		if (frm.doc.responsible_person) {
			frappe.db.get_value('Responsible Person', frm.doc.responsible_person, 'maintenance_team', function(r) {
				if (r && r.maintenance_team !== frm.doc.assigned_team) {
					frm.set_value('responsible_person', '');
				}
			});
		}
	},

	set_field_states: function(frm) {
		if (frm.doc.status === 'Closed' || frm.doc.status === 'Rejected') {
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

		// 2. Approved -> Assign
		if (frm.doc.status === 'Approved') {
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

