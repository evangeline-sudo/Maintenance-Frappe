const CATEGORY_MAINTENANCE_TYPE_MAP = {
	'IT Equipment': ['IT'],
	'Electrical Equipment': ['Non-IT'],
	'Vehicle': ['Non-IT'],
	'Machine': ['Non-IT'],
	'Furniture': ['Non-IT'],
	'Building/Facility': ['Non-IT'],
	'Office Equipment': ['Non-IT'],
	'Medical Equipment': ['Professional-Specialized'],
	'Other': ['Non-IT', 'IT', 'Professional-Specialized']
};

frappe.ui.form.on('Maintenance Request', {
	setup: function(frm) {
		frm.trigger('setup_queries');
	},

	setup_queries: function(frm) {
		frm.set_query('equipment', function() {
			return {
				query: 'maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request.get_equipment_for_category',
				filters: {
					equipment_category: frm.doc.equipment_category || ''
				}
			};
		});

		frm.set_query('unit_head', function() {
			return {
				query: 'maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request.get_manager_users'
			};
		});

		frm.set_query('assigned_to', function() {
			return {
				query: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_technician_users'
			};
		});

		frm.set_query('category', function() {
			let filters = { is_active: 1 };
			if (frm.doc.maintenance_type) {
				filters['maintenance_type'] = frm.doc.maintenance_type;
			}
			return { filters: filters };
		});

		frm.set_query('issue_category', function() {
			return {
				query: 'maintenance_frappe.maintenance_management.doctype.issue_category.issue_category.get_issue_categories',
				filters: {
					is_active: 1,
					equipment_category: frm.doc.equipment_category || ''
				}
			};
		});

		if (frm.fields_dict.location) {
			frm.set_query('location', function() {
				return { filters: { is_active: 1 } };
			});
		}

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
		if (frm.is_new() && !frm.doc.equipment_category) {
			frm.set_value('equipment_category', 'Other');
		}
		frm.trigger('autofill_employee_details');
		frm.trigger('update_maintenance_type_options');
		frm.trigger('setup_workflow_buttons');
		frm.trigger('set_field_states');
		frm.trigger('set_section_visibilities');
		if (frm.is_new() && !frm.doc.employee) {
			frm.trigger('auto_set_logged_in_employee');
		}
	},

	onload: function(frm) {
		if (frm.is_new() && !frm.doc.equipment_category) {
			frm.set_value('equipment_category', 'Other');
		}
		frm.trigger('autofill_employee_details');
		frm.trigger('update_maintenance_type_options');
		frm.trigger('set_section_visibilities');
		if (frm.is_new() && !frm.doc.employee) {
			frm.trigger('auto_set_logged_in_employee');
		}
	},

	auto_set_logged_in_employee: function(frm) {
		if (frm.is_new() && !frm.doc.employee) {
			frappe.call({
				method: 'maintenance_frappe.m_maintenance.doctype.maintenance_request.maintenance_request.get_logged_in_employee',
				callback: function(r) {
					if (r.message && r.message.name) {
						frm.set_value('employee', r.message.name);
					}
				}
			});
		}
	},

	autofill_employee_details: function(frm) {
		if (frm.is_new()) {
			if (!frm.doc.request_date) {
				frm.set_value('request_date', frappe.datetime.get_today());
			}
			if (!frm.doc.employee) {
				frappe.call({
					method: 'maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request.get_logged_in_employee_details',
					callback: function(r) {
						if (r.message) {
							let d = r.message;
							if (d.employee) {
								frm.set_value('employee', d.employee);
							}
							if (d.employee_name && !frm.doc.employee_name) {
								frm.set_value('employee_name', d.employee_name);
							}
							if (d.department && !frm.doc.department) {
								frm.set_value('department', d.department);
							}
							if (d.unit && !frm.doc.unit) {
								frm.set_value('unit', d.unit);
							}
							if (d.unit_head && !frm.doc.unit_head) {
								frm.set_value('unit_head', d.unit_head);
							}
							frm.trigger('set_field_states');
						}
					}
				});
			}
		}
	},

	ownership_type: function(frm) {
		frm.trigger('setup_queries');
	},

	maintenance_type: function(frm) {
		if (frm.doc.category) {
			frappe.db.get_value('Maintenance Category', frm.doc.category, 'maintenance_type').then(r => {
				if (r && r.message && r.message.maintenance_type && r.message.maintenance_type !== frm.doc.maintenance_type) {
					frm.set_value('category', null);
				}
			});
		}
		frm.trigger('setup_queries');
	},

	approval_status: function(frm) {
		if (frm.doc.approval_status === 'Approved') {
			if (['Draft', 'Submitted', 'Pending Approval', 'Pending', 'Hold'].includes(frm.doc.status)) {
				frm.set_value('status', 'Approved');
			}
		} else if (frm.doc.approval_status === 'Rejected') {
			frm.set_value('status', 'Rejected');
		} else if (frm.doc.approval_status === 'Hold') {
			frm.set_value('status', 'On Hold');
		} else if (frm.doc.approval_status === 'Pending') {
			if (['Draft', 'Submitted'].includes(frm.doc.status)) {
				frm.set_value('status', 'Pending Approval');
			}
		}
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

		// Check if current equipment matches the new category; if not, clear it
		if (frm.doc.equipment && frm.doc.equipment_category) {
			frappe.call({
				method: 'maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request.get_matching_equipment_categories',
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
						}
					});
				}
			});
		}
	},

	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.call({
				method: 'maintenance_frappe.maintenance_management.doctype.maintenance_request.maintenance_request.get_employee_manager_user',
				args: {
					employee: frm.doc.employee
				},
				callback: function(r) {
					if (r.message) {
						if (r.message.employee_name) {
							frm.set_value('employee_name', r.message.employee_name);
						}
						if (r.message.department) {
							frm.set_value('department', r.message.department);
						}
						if (r.message.unit) {
							frm.set_value('unit', r.message.unit);
						}
						if (r.message.user_id) {
							frm.set_value('unit_head', r.message.user_id);
						}
						if (r.message.department && !frm.doc.department) {
							frm.set_value('department', r.message.department);
						}
						if (r.message.unit && !frm.doc.unit) {
							frm.set_value('unit', r.message.unit);
						}
						frm.trigger('set_field_states');
					}
				}
			});
		} else {
			frm.set_value('employee_name', '');
			frm.set_value('department', '');
			frm.set_value('unit', '');
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
						
					}
					if (eq.location) {
						frm.set_value('equipment_location', eq.location);

						
						if (!frm.doc.location) {
							frm.set_value('location', eq.location);
						}
					}
					if (frm.fields_dict.asset && eq.asset_id && !frm.doc.asset) {
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
			
			
		}
	},

	set_section_visibilities: function(frm) {
		/**
		 * Four Role-based Visibility Tiers:
		 *   1. Maintenance Manager: Full system access & control over all fields/sections.
		 *   2. Maintenance User (Technician): Work execution, work logs, parts used & resolution editable.
		 *   3. Manager : Department/unit review, approval & assignment fields.
		 *   4. Employee (Employee Portal):
		 *      Visible: title, equipment_category (Category), issue_category (Issue Category),
		 *               priority (Priority), employee_name, department, unit,
		 *               request_date, responsible_person (Responsible), description
		 *      Hidden:  employee (internal link), ownership_type, maintenance_type, status,
		 *               cost totals, technical/approval sections
		 */
		let user_roles = frappe.user_roles || [];
		let current_user = frappe.session.user;

		let is_full_access = (
			current_user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Maintenance Manager') ||
			user_roles.includes('Maintenance User') ||
			user_roles.includes('Manager') ||
			user_roles.includes('Technician') ||
			(frm.doc.unit_head && current_user === frm.doc.unit_head)
		);

		let employee_only = !is_full_access;

		// ── Fields hidden for Employee-only ─────────────────────────────────────
		['employee', 'ownership_type', 'maintenance_type', 'status',
		 'total_parts_cost', 'total_labour_cost', 'total_maintenance_cost'
		].forEach(function(f) {
			frm.set_df_property(f, 'hidden', employee_only ? 1 : 0);
		});

		// ── Fields visible for Employee Portal ──────────────────────────────────
		['title', 'equipment_category', 'issue_category', 'priority',
		 'employee_name', 'department', 'unit', 'request_date', 'responsible_person', 'description'
		].forEach(function(f) {
			frm.set_df_property(f, 'hidden', 0);
		});

		// ── Sections hidden for Employee-only ────────────────────────────────────
		['section_maintenance_details',
		 'section_equipment_details',
		 'section_non_organizational_details',
		 'section_approval_assignment',
		 'section_diagnosis',
		 'section_work_details',
		 'section_resolution',
		 'section_verification',
		 'section_closure'
		].forEach(function(section) {
			frm.set_df_property(section, 'hidden', employee_only ? 1 : 0);
		});

		// Status history table always hidden for employee-only
		frm.set_df_property('status_history', 'hidden', employee_only ? 1 : 0);

		// ── Requester fields: read-only for everyone (auto-filled) ───────────────
		['employee_name', 'department', 'unit', 'request_date', 'responsible_person'].forEach(function(f) {
			frm.set_df_property(f, 'read_only', 1);
		});

		// ── Apply technician-specific restrictions on top of the above ───────────
		frm.trigger('apply_technician_restrictions');
	},

	apply_technician_restrictions: function(frm) {
		/**
		 * When the current user is the assigned technician (and not an admin/manager/approver),
		 * make the following sections read-only:
		 *   - Verification section
		 *   - Diagnosis section
		 *   - Approval & Assignment section
		 *   - Closure section
		 *
		 * The technician can still edit:
		 *   - Work Details (work_logs, parts_used)
		 *   - Resolution (resolution_notes, root_cause)
		 */
		let user_roles = frappe.user_roles || [];
		let current_user = frappe.session.user;

		// Check if the current user is the assigned technician
		let is_assigned_technician = (
			frm.doc.assigned_to &&
			current_user === frm.doc.assigned_to
		);

		// Check if the current user has elevated (admin/approver) privileges
		let is_privileged = (
			current_user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Maintenance Manager') ||
			user_roles.includes('Manager') ||
			(frm.doc.unit_head && current_user === frm.doc.unit_head)
		);

		// Only apply technician restrictions if assigned technician and not a privileged user
		if (is_assigned_technician && !is_privileged) {
			// --- Approval & Assignment section: fully read-only for technician ---
			let approval_assignment_fields = [
				'unit_head', 'approval_status', 'approval_date',
				'approval_notes', 'assigned_to', 'assigned_date'
			];
			approval_assignment_fields.forEach(function(fieldname) {
				frm.set_df_property(fieldname, 'read_only', 1);
			});

			// --- Diagnosis section: read-only for technician ---
			let diagnosis_fields = [
				'diagnosis_notes', 'estimated_completion_time', 'estimated_cost'
			];
			diagnosis_fields.forEach(function(fieldname) {
				frm.set_df_property(fieldname, 'read_only', 1);
			});

			// --- Verification section: read-only for technician ---
			let verification_fields = [
				'verification_status', 'verification_feedback', 'verification_date'
			];
			verification_fields.forEach(function(fieldname) {
				frm.set_df_property(fieldname, 'read_only', 1);
			});

			// --- Closure section: read-only for technician ---
			let closure_fields = [
				'closed_date', 'verified_by', 'closing_remarks'
			];
			closure_fields.forEach(function(fieldname) {
				frm.set_df_property(fieldname, 'read_only', 1);
			});
		}
	},

	set_field_states: function(frm) {
		let user_roles = frappe.user_roles || [];
		let is_authorized_approver = (
			frappe.session.user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Manager') ||
			user_roles.includes('Maintenance Manager') ||
			user_roles.includes('Employee') ||
			(frm.doc.unit_head && frappe.session.user === frm.doc.unit_head)
		);

		// Requester details are read-only so users cannot alter their logged-in requester info
		frm.set_df_property('employee', 'read_only', 1);
		frm.set_df_property('employee_name', 'read_only', 1);
		frm.set_df_property('department', 'read_only', 1);
		frm.set_df_property('unit', 'read_only', 1);
		frm.set_df_property('request_date', 'read_only', 1);

		// Approval Status & Verification Status can be changed directly by Admin, Maintenance Manager, or Unit Head
		frm.set_df_property('approval_status', 'read_only', is_authorized_approver ? 0 : 1);
		frm.set_df_property('verification_status', 'read_only', is_authorized_approver ? 0 : 1);

		// Hide redundant status field on form view
		frm.set_df_property('status', 'hidden', 1);

		// Apply technician-specific read-only restrictions
		frm.trigger('apply_technician_restrictions');
	},

	setup_workflow_buttons: function(frm) {
		if (frm.is_new()) return;

		let user_roles = frappe.user_roles || [];
		let can_approve = (
			frappe.session.user === 'Administrator' ||
			user_roles.includes('System Manager') ||
			user_roles.includes('Manager') ||
			user_roles.includes('Maintenance Manager') ||
			(frm.doc.manager && frappe.session.user === frm.doc.manager)
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
						options: 'Employee',
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

