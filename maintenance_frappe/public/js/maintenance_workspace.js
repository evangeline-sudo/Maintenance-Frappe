// Maintenance Workspace Employee Approvals Component
// Copyright (c) 2026, Evangeline and contributors

(function() {
	'use strict';

	let currentTab = 'pending';
	let cachedData = null;
	let isFetching = false;

	function is_maintenance_workspace() {
		const route = frappe.get_route ? frappe.get_route() : [];
		if (!route || !route.length) return false;

		const first = (route[0] || '').toLowerCase();
		const second = (route[1] || '').toLowerCase();

		if (first === 'desk' && second === 'maintenance') return true;
		if ((first === 'workspaces' || first === 'workspace') && second === 'maintenance') return true;

		// Fallback check on active document title or route path
		if (window.location.hash.includes('maintenance') || window.location.pathname.includes('/desk/maintenance')) {
			return true;
		}

		return false;
	}

	function get_workspace_mount_point() {
		// Try finding the workspace page content container
		let $container = $('.workspace-page:visible .layout-main-section, [data-page-route="Workspaces"]:visible .layout-main-section, .layout-main-section:visible, .page-content:visible').first();
		if ($container.length) return $container;

		// Fallback to body container
		return $('#body').first();
	}

	function init_employee_approvals_workspace() {
		if (!is_maintenance_workspace()) {
			$('#maintenance-approvals-section').remove();
			return;
		}

		const $mount = get_workspace_mount_point();
		if (!$mount || !$mount.length) {
			setTimeout(init_employee_approvals_workspace, 300);
			return;
		}

		if (!$('#maintenance-approvals-section').length) {
			const skeletonHtml = `
				<div id="maintenance-approvals-section" class="maintenance-approvals-container">
					<div class="maintenance-approvals-header">
						<div class="maintenance-header-title-area">
							<h3 class="maintenance-approvals-title">
								<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
								My Approvals & Requests
							</h3>
							<p class="maintenance-approvals-subtitle">Track, review, and manage your maintenance requests across approval stages</p>
						</div>
						<div class="maintenance-header-actions">
							<button class="btn btn-primary btn-sm btn-new-request" style="display:inline-flex;align-items:center;gap:6px;">
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
								+ New Maintenance Request
							</button>
							<button class="btn btn-default btn-sm btn-view-all">View All</button>
							<button class="btn btn-default btn-sm btn-refresh-approvals" title="Refresh">
								<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
							</button>
						</div>
					</div>

					<div class="maintenance-tabs-wrapper">
						<button class="maintenance-tab-btn active" data-tab="pending">
							Pending Approvals <span class="tab-badge tab-badge-pending" id="badge-pending-count">0</span>
						</button>
						<button class="maintenance-tab-btn" data-tab="approved">
							Approved Requests <span class="tab-badge tab-badge-approved" id="badge-approved-count">0</span>
						</button>
						<button class="maintenance-tab-btn" data-tab="all">
							All Requests <span class="tab-badge tab-badge-all" id="badge-all-count">0</span>
						</button>
					</div>

					<div id="maintenance-cards-content" class="maintenance-cards-grid">
						<div style="padding: 24px; text-align: center; color: var(--text-muted); width: 100%;">
							<div class="spinner-border spinner-border-sm" role="status"></div> Loading approvals...
						</div>
					</div>
				</div>
			`;

			// Prepend before metrics or existing workspace cards
			$mount.prepend(skeletonHtml);
			bind_header_events();
		}

		fetch_and_render_approvals();
	}

	function bind_header_events() {
		const $section = $('#maintenance-approvals-section');

		$section.on('click', '.btn-new-request', function(e) {
			e.preventDefault();
			frappe.new_doc('Maintenance Request');
		});

		$section.on('click', '.btn-view-all', function(e) {
			e.preventDefault();
			frappe.set_route('List', 'Maintenance Request');
		});

		$section.on('click', '.btn-refresh-approvals', function(e) {
			e.preventDefault();
			const $btn = $(this);
			$btn.find('svg').css('animation', 'spin 0.8s linear infinite');
			fetch_and_render_approvals(() => {
				$btn.find('svg').css('animation', 'none');
			});
		});

		$section.on('click', '.maintenance-tab-btn', function() {
			$('.maintenance-tab-btn').removeClass('active');
			$(this).addClass('active');
			currentTab = $(this).data('tab');
			render_cards();
		});

		$section.on('click', '.card-link-trigger', function(e) {
			e.preventDefault();
			const docname = $(this).data('name');
			if (docname) {
				frappe.set_route('Form', 'Maintenance Request', docname);
			}
		});

		// Quick approve / reject triggers
		$section.on('click', '.btn-quick-approve', function(e) {
			e.stopPropagation();
			const docname = $(this).data('name');
			frappe.prompt({
				fieldname: 'notes',
				fieldtype: 'Small Text',
				label: __('Approval Remarks')
			}, function(values) {
				frappe.call({
					method: 'maintenance_frappe.api.maintenance.approve_maintenance_request',
					args: {
						request_id: docname,
						notes: values.notes || ''
					},
					callback: function(r) {
						if (!r.exc) {
							frappe.show_alert({ message: __('Request approved successfully'), indicator: 'green' });
							fetch_and_render_approvals();
						}
					}
				});
			}, __('Approve Request: ') + docname, __('Approve'));
		});

		$section.on('click', '.btn-quick-reject', function(e) {
			e.stopPropagation();
			const docname = $(this).data('name');
			frappe.prompt({
				fieldname: 'notes',
				fieldtype: 'Small Text',
				label: __('Rejection Reason'),
				reqd: 1
			}, function(values) {
				frappe.call({
					method: 'maintenance_frappe.api.maintenance.reject_maintenance_request',
					args: {
						request_id: docname,
						notes: values.notes || ''
					},
					callback: function(r) {
						if (!r.exc) {
							frappe.show_alert({ message: __('Request rejected'), indicator: 'orange' });
							fetch_and_render_approvals();
						}
					}
				});
			}, __('Reject Request: ') + docname, __('Reject'));
		});
	}

	function fetch_and_render_approvals(callback) {
		if (isFetching) return;
		isFetching = true;

		frappe.call({
			method: 'maintenance_frappe.api.maintenance.get_employee_workspace_approvals',
			callback: function(r) {
				isFetching = false;
				if (r.message) {
					cachedData = r.message;
					$('#badge-pending-count').text(cachedData.counts.pending || 0);
					$('#badge-approved-count').text(cachedData.counts.approved || 0);
					$('#badge-all-count').text(cachedData.counts.total || 0);
					render_cards();
				}
				if (callback) callback();
			},
			error: function() {
				isFetching = false;
				if (callback) callback();
			}
		});
	}

	function render_cards() {
		const $content = $('#maintenance-cards-content');
		if (!$content.length) return;

		if (!cachedData) {
			$content.html('<div style="padding:24px;text-align:center;color:var(--text-muted);width:100%;">Loading approvals...</div>');
			return;
		}

		let items = [];
		if (currentTab === 'pending') {
			items = cachedData.pending || [];
		} else if (currentTab === 'approved') {
			items = cachedData.approved || [];
		} else {
			items = (cachedData.pending || []).concat(cachedData.approved || []);
		}

		if (!items.length) {
			render_empty_state($content);
			return;
		}

		let cardsHtml = '';
		items.forEach(item => {
			const isPending = item.approval_status === 'Pending';
			const statusBadgeClass = isPending ? 'status-pill-pending' : (item.status === 'Resolved' || item.status === 'Closed' ? 'status-pill-resolved' : 'status-pill-approved');
			const priorityClass = 'priority-' + (item.priority_color || 'secondary');

			let actionButtons = `
				<button class="btn btn-default btn-xs card-link-trigger" data-name="${item.name}" style="font-weight:600;">
					View Details &rarr;
				</button>
			`;

			if (item.can_approve) {
				actionButtons = `
					<div style="display:flex;gap:6px;">
						<button class="btn btn-primary btn-xs btn-quick-approve" data-name="${item.name}">Approve</button>
						<button class="btn btn-danger btn-xs btn-quick-reject" data-name="${item.name}">Reject</button>
					</div>
					<button class="btn btn-default btn-xs card-link-trigger" data-name="${item.name}" style="font-weight:600;">
						Details &rarr;
					</button>
				`;
			}

			cardsHtml += `
				<div class="maintenance-approval-card">
					<div>
						<div class="maintenance-card-top">
							<a href="#Form/Maintenance Request/${item.name}" class="maintenance-card-id card-link-trigger" data-name="${item.name}">
								${item.name}
							</a>
							<div class="maintenance-card-badges">
								<span class="priority-tag ${priorityClass}">${item.priority}</span>
								<span class="status-pill ${statusBadgeClass}">${item.approval_status}</span>
							</div>
						</div>

						<h4 class="maintenance-card-title">${frappe.utils.escape_html(item.title)}</h4>
						<p class="maintenance-card-desc">${frappe.utils.escape_html(item.description)}</p>

						<div class="maintenance-card-meta">
							<div class="meta-row">
								<span class="meta-label">
									<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
									Equipment:
								</span>
								<span class="meta-value" title="${frappe.utils.escape_html(item.equipment_name)}">${frappe.utils.escape_html(item.equipment_name)}</span>
							</div>
							<div class="meta-row">
								<span class="meta-label">
									<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
									Submitted:
								</span>
								<span class="meta-value">${item.date || '-'}</span>
							</div>
							<div class="meta-row">
								<span class="meta-label">
									<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
									Approver:
								</span>
								<span class="meta-value" title="${frappe.utils.escape_html(item.approver)}">${frappe.utils.escape_html(item.approver)}</span>
							</div>
							<div class="meta-row">
								<span class="meta-label">Current Stage:</span>
								<span class="meta-value" style="color:var(--primary-color);">${item.status}</span>
							</div>
						</div>
					</div>

					<div class="maintenance-card-actions">
						${actionButtons}
					</div>
				</div>
			`;
		});

		$content.html(cardsHtml);
	}

	function render_empty_state($content) {
		if (currentTab === 'pending') {
			$content.html(`
				<div class="maintenance-empty-state" style="grid-column: 1 / -1;">
					<div class="empty-state-icon empty-icon-pending">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
					</div>
					<h4 class="empty-state-title">No Pending Approvals</h4>
					<p class="empty-state-text">You have no maintenance requests currently awaiting action or review.</p>
					<button class="btn btn-primary btn-sm btn-new-request" style="display:inline-flex;align-items:center;gap:6px;">
						+ New Maintenance Request
					</button>
				</div>
			`);
		} else if (currentTab === 'approved') {
			$content.html(`
				<div class="maintenance-empty-state" style="grid-column: 1 / -1;">
					<div class="empty-state-icon empty-icon-approved">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
					</div>
					<h4 class="empty-state-title">No Approved Requests Yet</h4>
					<p class="empty-state-text">Requests that have completed manager review and are approved will be displayed here.</p>
					<button class="btn btn-default btn-sm btn-view-all">View All Requests</button>
				</div>
			`);
		} else {
			$content.html(`
				<div class="maintenance-empty-state" style="grid-column: 1 / -1;">
					<div class="empty-state-icon empty-icon-pending">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
					</div>
					<h4 class="empty-state-title">No Maintenance Requests Found</h4>
					<p class="empty-state-text">You haven't submitted any maintenance requests yet.</p>
					<button class="btn btn-primary btn-sm btn-new-request">Create First Request</button>
				</div>
			`);
		}
	}

	// Hook into Frappe page router & Desk events
	$(document).on('app_ready', function() {
		setTimeout(init_employee_approvals_workspace, 200);
	});

	if (window.frappe && frappe.router) {
		frappe.router.on('change', function() {
			setTimeout(init_employee_approvals_workspace, 150);
		});
	}

	// Also monitor document title & hash changes
	window.addEventListener('hashchange', function() {
		setTimeout(init_employee_approvals_workspace, 150);
	});

})();

