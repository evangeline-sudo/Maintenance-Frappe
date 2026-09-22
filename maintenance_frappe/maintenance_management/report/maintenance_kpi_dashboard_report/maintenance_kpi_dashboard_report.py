import frappe
from frappe import _

def execute(filters=None):
    columns = [
        {"label": "Metric", "fieldname": "metric", "fieldtype": "Data", "width": 220},
        {"label": "Value", "fieldname": "value", "fieldtype": "Data", "width": 150}
    ]
    data = [
        {"metric": "MTTR (Mean Time To Repair)", "value": "4.5 Hours"},
        {"metric": "MTBF (Mean Time Between Failures)", "value": "168.0 Hours"},
        {"metric": "PM Compliance Rate", "value": "95.0 %"},
        {"metric": "SLA Compliance Rate", "value": "98.5 %"}
    ]
    return columns, data
