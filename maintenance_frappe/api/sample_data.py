import frappe
from frappe.utils import now_datetime, today, add_days

def create_sample_data():
    """Create comprehensive sample data for Maintenance module including 4 Maintenance Requests."""
    # 1. Fetch available employees
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "department", "user_id"],
        limit=5
    )
    if not employees:
        employees = frappe.get_all(
            "Employee",
            fields=["name", "employee_name", "department", "user_id"],
            limit=5
        )

    emp1 = employees[0] if len(employees) > 0 else None
    emp2 = employees[1] if len(employees) > 1 else emp1
    emp3 = employees[2] if len(employees) > 2 else emp1
    emp4 = employees[3] if len(employees) > 3 else emp1

    # Fetch manager / unit_head user
    manager_users = frappe.db.sql_list("""
        SELECT DISTINCT parent FROM `tabHas Role`
        WHERE role IN ('Manager', 'Maintenance Manager', 'System Manager')
        AND parent NOT IN ('Administrator', 'Guest')
        LIMIT 2
    """)
    approver_user = manager_users[0] if manager_users else "Administrator"

    # Fetch technician / maintenance user
    tech_users = frappe.db.sql_list("""
        SELECT DISTINCT parent FROM `tabHas Role`
        WHERE role IN ('Technician', 'Maintenance Technician', 'Maintenance User')
        AND parent NOT IN ('Administrator', 'Guest')
        LIMIT 2
    """)
    technician_user = tech_users[0] if tech_users else approver_user

    # 2. Ensure Maintenance Teams exist
    teams_data = [
        {"team_name": "IT Support Team", "team_code": "TEAM-IT", "team_lead": emp1.get("name") if emp1 else None},
        {"team_name": "Electrical Maintenance Team", "team_code": "TEAM-ELEC", "team_lead": emp2.get("name") if emp2 else None},
        {"team_name": "Facility & General Maintenance Team", "team_code": "TEAM-FAC", "team_lead": emp3.get("name") if emp3 else None},
    ]
    created_teams = {}
    for td in teams_data:
        team_name = td["team_name"]
        if not frappe.db.exists("Maintenance Team", team_name):
            doc = frappe.get_doc({
                "doctype": "Maintenance Team",
                "team_name": team_name,
                "team_code": td["team_code"],
                "team_lead": td["team_lead"],
                "is_active": 1,
            })
            if td["team_lead"]:
                doc.append("team_members", {
                    "employee": td["team_lead"],
                    "employee_name": frappe.db.get_value("Employee", td["team_lead"], "employee_name"),
                    "role": "Team Lead"
                })
            doc.insert(ignore_permissions=True)
            created_teams[team_name] = doc.name
        else:
            created_teams[team_name] = team_name

    # 3. Ensure Issue Categories exist
    issues_data = [
        {"issue_category_name": "Power Supply Fault", "equipment_category": "IT Equipment", "description": "Faulty SMPS / Redundant PSU failure"},
        {"issue_category_name": "Sensor / Controller Fault", "equipment_category": "Electrical Equipment", "description": "AMF controller or sensor readout fault"},
        {"issue_category_name": "Motor Vibration / Bearing Fault", "equipment_category": "Machine", "description": "Excessive motor vibration, misalignment or bearing wear"},
        {"issue_category_name": "Paper Jam & Feeder Roller Wear", "equipment_category": "Office Equipment", "description": "Duplex jam or paper feeder roller slipping"},
    ]
    created_issues = {}
    for idata in issues_data:
        ic_name = idata["issue_category_name"]
        existing = frappe.db.exists("Issue Category", {"issue_category_name": ic_name})
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Issue Category",
                "issue_category_name": ic_name,
                "equipment_category": idata["equipment_category"],
                "description": idata["description"],
                "is_active": 1
            })
            doc.insert(ignore_permissions=True)
            created_issues[ic_name] = doc.name
        else:
            created_issues[ic_name] = existing

    # 4. Ensure Equipment records exist
    equipment_data = [
        {
            "equipment_id": "EQ-IT-001",
            "equipment_name": "Dell PowerEdge R740 Rack Server",
            "equipment_category": "IT Equipment",
            "maintenance_type": "IT",
            "used_in_location": "Server Room A - Rack 02",
            "serial_number": "DELL-PE-740-9821",
            "status": "Active",
            "maintenance_team": "IT Support Team",
            "responsible_person": emp1.get("name") if emp1 else None,
            "department": emp1.get("department") if emp1 else None
        },
        {
            "equipment_id": "EQ-ELEC-001",
            "equipment_name": "Cummins 250kVA Silent Diesel Generator",
            "equipment_category": "Electrical Equipment",
            "maintenance_type": "Non-IT",
            "used_in_location": "Main DG Yard",
            "serial_number": "CUM-DG-250-4410",
            "status": "Active",
            "maintenance_team": "Electrical Maintenance Team",
            "responsible_person": emp2.get("name") if emp2 else None,
            "department": emp2.get("department") if emp2 else None
        },
        {
            "equipment_id": "EQ-MACH-001",
            "equipment_name": "Siemens 15HP Heavy Duty Induction Motor",
            "equipment_category": "Machine",
            "maintenance_type": "Non-IT",
            "used_in_location": "Production Floor - Line 1",
            "serial_number": "SIE-MOT-15HP-8832",
            "status": "Under Maintenance",
            "maintenance_team": "Facility & General Maintenance Team",
            "responsible_person": emp3.get("name") if emp3 else None,
            "department": emp3.get("department") if emp3 else None
        },
        {
            "equipment_id": "EQ-OFF-001",
            "equipment_name": "HP Color LaserJet Enterprise MFP E87650",
            "equipment_category": "Office Equipment",
            "maintenance_type": "Non-IT",
            "used_in_location": "Admin Block - 2nd Floor",
            "serial_number": "HP-MFP-8765-1102",
            "status": "Active",
            "maintenance_team": "IT Support Team",
            "responsible_person": emp4.get("name") if emp4 else None,
            "department": emp4.get("department") if emp4 else None
        }
    ]

    created_equipment = {}
    for eq in equipment_data:
        existing = frappe.db.exists("Equipment", {"equipment_id": eq["equipment_id"]})
        if not existing:
            existing = frappe.db.exists("Equipment", {"equipment_name": eq["equipment_name"]})
        if not existing:
            doc = frappe.get_doc({
                "doctype": "Equipment",
                "equipment_id": eq["equipment_id"],
                "equipment_name": eq["equipment_name"],
                "equipment_category": eq["equipment_category"],
                "maintenance_type": eq["maintenance_type"],
                "used_in_location": eq["used_in_location"],
                "serial_number": eq["serial_number"],
                "status": eq["status"],
                "maintenance_team": eq["maintenance_team"],
                "responsible_person": eq["responsible_person"],
                "department": eq["department"]
            })
            doc.insert(ignore_permissions=True)
            created_equipment[eq["equipment_id"]] = doc.name
        else:
            created_equipment[eq["equipment_id"]] = existing

    # 5. Create 4 Sample Maintenance Requests
    now = now_datetime()
    today_date = today()

    requests_to_create = [
        # Request 1: Pending Approval
        {
            "title": "Dell Server R740 secondary power supply fault",
            "description": "The redundant power supply unit (PSU 2) on Dell PowerEdge R740 in Server Room Rack 02 is showing an amber LED error code. Primary PSU 1 is currently bearing the full load. Urgent replacement is required to maintain system redundancy.",
            "employee": emp1.get("name") if emp1 else None,
            "employee_name": emp1.get("employee_name") if emp1 else "Dharma S",
            "department": emp1.get("department") if emp1 else "IT",
            "request_date": today_date,
            "equipment": created_equipment.get("EQ-IT-001"),
            "equipment_name": "Dell PowerEdge R740 Rack Server",
            "equipment_category": "IT Equipment",
            "issue_category": created_issues.get("Power Supply Fault"),
            "priority": 4,
            "ownership_type": "Organizational Asset",
            "maintenance_type": "IT",
            "status": "Pending Approval",
            "approval_status": "Pending",
            "unit_head": approver_user,
        },
        # Request 2: Approved and Assigned
        {
            "title": "Emergency AMF panel sensor calibration on 250kVA DG set",
            "description": "During the routine test sequence, the automatic mains failure (AMF) controller displayed a voltage frequency sensor mismatch. Sensor communication timeout occurred twice. Requires wiring check and sensor recalibration.",
            "employee": emp2.get("name") if emp2 else None,
            "employee_name": emp2.get("employee_name") if emp2 else "Alex Kevin S",
            "department": emp2.get("department") if emp2 else "Operations",
            "request_date": today_date,
            "equipment": created_equipment.get("EQ-ELEC-001"),
            "equipment_name": "Cummins 250kVA Silent Diesel Generator",
            "equipment_category": "Electrical Equipment",
            "issue_category": created_issues.get("Sensor / Controller Fault"),
            "priority": 5,
            "ownership_type": "Organizational Asset",
            "maintenance_type": "Non-IT",
            "status": "Assigned",
            "approval_status": "Approved",
            "unit_head": approver_user,
            "approval_date": now,
            "approval_notes": "Approved for immediate inspection. Ensure generator is switched to manual isolation mode before opening panel.",
            "assigned_team": "Electrical Maintenance Team",
            "assigned_to": technician_user,
            "assigned_date": now,
            "responsible_person": emp2.get("name") if emp2 else None
        },
        # Request 3: In Progress with Diagnosis
        {
            "title": "Siemens 15HP induction motor abnormal vibration and bearing noise",
            "description": "Excessive vibration and overheating reported on the main production conveyor drive motor. Vibration analysis indicated bearing wear and minor shaft misalignment.",
            "employee": emp3.get("name") if emp3 else None,
            "employee_name": emp3.get("employee_name") if emp3 else "Aravind D",
            "department": emp3.get("department") if emp3 else "Production",
            "request_date": today_date,
            "equipment": created_equipment.get("EQ-MACH-001"),
            "equipment_name": "Siemens 15HP Heavy Duty Induction Motor",
            "equipment_category": "Machine",
            "issue_category": created_issues.get("Motor Vibration / Bearing Fault"),
            "priority": 3,
            "ownership_type": "Organizational Asset",
            "maintenance_type": "Non-IT",
            "status": "In Progress",
            "approval_status": "Approved",
            "unit_head": approver_user,
            "approval_date": now,
            "approval_notes": "Approved. Schedule repair during planned production changeover.",
            "assigned_team": "Facility & General Maintenance Team",
            "assigned_to": technician_user,
            "assigned_date": now,
            "responsible_person": emp3.get("name") if emp3 else None,
            "diagnosis_notes": "Front roller bearing race scored. Radial clearance exceeded threshold by 0.15mm. Laser alignment needed.",
            "estimated_cost": 4500.0,
            "estimated_completion_time": add_days(now, 1)
        },
        # Request 4: Resolved / Completed
        {
            "title": "HP Enterprise MFP duplex unit jamming and squeaking roller",
            "description": "Frequent multi-sheet feeding and paper jams in the duplex reversal tray on 2nd floor copier. Squeaking noise when paper passes through the registration rollers.",
            "employee": emp4.get("name") if emp4 else None,
            "employee_name": emp4.get("employee_name") if emp4 else "Nithish Joe G",
            "department": emp4.get("department") if emp4 else "Administration",
            "request_date": today_date,
            "equipment": created_equipment.get("EQ-OFF-001"),
            "equipment_name": "HP Color LaserJet Enterprise MFP E87650",
            "equipment_category": "Office Equipment",
            "issue_category": created_issues.get("Paper Jam & Feeder Roller Wear"),
            "priority": 2,
            "ownership_type": "Organizational Asset",
            "maintenance_type": "Non-IT",
            "status": "Resolved",
            "approval_status": "Approved",
            "unit_head": approver_user,
            "approval_date": now,
            "approval_notes": "Approved for maintenance team inspection and roller replacement.",
            "assigned_team": "IT Support Team",
            "assigned_to": technician_user,
            "assigned_date": now,
            "responsible_person": emp1.get("name") if emp1 else None,
            "diagnosis_notes": "Pick-up and separation rollers coated with paper dust and glazed.",
            "resolution_date": now,
            "resolution_notes": "Replaced worn pickup and separation roller kit (Part #RM2-5576). Cleaned duplex paper transport sensors and lubricated drive gear cluster. Printed 100 test duplex copies without paper jams.",
            "root_cause": "Normal wear and tear of rubber friction rollers after 120,000 cycles.",
            "verification_status": "Verified",
            "verification_feedback": "Duplex printing tested and operating smoothly.",
            "verification_date": now
        }
    ]

    created_requests = []
    for req_data in requests_to_create:
        doc = frappe.new_doc("Maintenance Request")
        doc.update(req_data)
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory = False
        doc.insert(ignore_permissions=True)
        created_requests.append({
            "name": doc.name,
            "title": doc.title,
            "category": doc.equipment_category,
            "status": doc.status,
            "approval_status": doc.approval_status
        })

    frappe.db.commit()
    print("SUCCESS: Created sample maintenance data!")
    print("Teams:", list(created_teams.keys()))
    print("Equipment:", list(created_equipment.keys()))
    print("Maintenance Requests Created:", created_requests)
    return created_requests
