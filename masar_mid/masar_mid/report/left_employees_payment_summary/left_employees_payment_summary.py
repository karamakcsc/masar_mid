import frappe
from frappe.utils import getdate, cint
import calendar
def execute(filters=None):
    if not filters:
        filters = {}

    summary_type = filters.get("summary_type", "Yearly")
    year = cint(filters.get("year")) if filters.get("year") else None
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    if from_date and to_date:
        if getdate(from_date) > getdate(to_date):
            frappe.throw("<b>From Date</b> cannot be later than <b>To Date</b>.")
    elif from_date and not to_date:
        frappe.throw("Please select both <b>From Date</b> and <b>To Date</b>.")
    elif to_date and not from_date:
        frappe.throw("Please select both <b>From Date</b> and <b>To Date</b>.")
    conditions = ["emp.status = 'Left'", "ss.docstatus = 1"]
    if year:
        conditions.append("YEAR(ss.start_date) = %(year)s")
    if filters.get("department"):
        conditions.append("emp.department = %(department)s")
    if from_date and to_date:
        conditions.append("emp.relieving_date BETWEEN %(from_date)s AND %(to_date)s")
    if filters.get("employee"):
        conditions.append("emp.name = %(employee)s")
    if filters.get("designation"):
        conditions.append("emp.designation = %(designation)s")
        
    where_clause = " AND ".join(conditions)
    records = frappe.db.sql(f"""
        SELECT
            emp.name AS employee_id,
            emp.employee_name,
            emp.department,
            emp.designation,
            emp.date_of_joining,
            emp.relieving_date,
            YEAR(ss.start_date) AS year,
            MONTH(ss.start_date) AS month,
            SUM(ss.net_pay) AS net_pay
        FROM `tabSalary Slip` ss
        INNER JOIN `tabEmployee` emp ON ss.employee = emp.name
        WHERE {where_clause}
        GROUP BY emp.name, YEAR(ss.start_date), MONTH(ss.start_date)
        ORDER BY emp.employee_name
    """, filters, as_dict=True)
    data_map = {}
    period_labels = []
    for r in records:
        key = r.employee_id
        if key not in data_map:
            data_map[key] = {
                "employee_id": r.employee_id,
                "employee_name": r.employee_name,
                "department": r.department,
                "designation": r.designation,
                "date_of_joining": r.date_of_joining,
                "relieving_date": r.relieving_date,
            }
        if summary_type == "Yearly":
            label = str(r.year)
        else:
            label = calendar.month_abbr[r.month]
        data_map[key][label] = data_map[key].get(label, 0) + float(r.net_pay or 0)
        if label not in period_labels:
            period_labels.append(label)
    period_labels = sorted(period_labels, key=lambda x: (
        int(x) if x.isdigit() else list(calendar.month_abbr).index(x)
    ))
    data = list(data_map.values())
    columns = [
        {"label": "Employee", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 120},
        {"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 120},
        {"label": "Date of Joining", "fieldname": "date_of_joining", "fieldtype": "Date", "width": 100},
        {"label": "Relieving Date", "fieldname": "relieving_date", "fieldtype": "Date", "width": 100},
    ]
    for lbl in period_labels:
        columns.append({
            "label": lbl,
            "fieldname": lbl,
            "fieldtype": "Currency",
            "width": 100
        })
    for row in data:
        row["Total"] = sum(row.get(lbl, 0) for lbl in period_labels)
    columns.append({"label": "Total", "fieldname": "Total", "fieldtype": "Currency", "width": 120})
    total_paid = sum(r["Total"] for r in data)
    report_summary = [
        {"label": "Total Net Pay", "value": total_paid, "indicator": "green"}
    ]
    return columns, data, None, report_summary
