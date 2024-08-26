# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = ""
    _from, to = filters.get('from_date'), filters.get('to_date')
 
    if filters.get('salary_component'):
        conditions += f" AND test.salary_component = '{filters.get('salary_component')}'"

    if filters.get('is_active'):
        conditions += f" AND test.is_active = '{filters.get('is_active')}'"

    if filters.get('employee'):
        conditions += f" AND te.employee = '{filters.get('employee')}'"
        
    if filters.get('esc_amount'):
        conditions += f" AND test.esc_amount = '{filters.get('esc_amount')}'"
        
    if filters.get('status'):
        conditions += f" AND te.status = '{filters.get('status')}'"
	
    if _from and to:
        conditions += f" AND test.date BETWEEN '{_from}' AND '{to}'"
			
    return frappe.db.sql(f"""
        SELECT te.employee, te.employee_name, test.salary_component, test.esc_amount, test.date, test.is_active, te.status, test.remarks 
        FROM `tabEmployee` te 
        INNER JOIN `tabEmployee Salary Table` test ON test.parent = te.name
        WHERE 1=1 {conditions}
        ORDER BY te.employee
    """)

def columns():
    return [
        "Employee:Link/Employee:200",
        "Employee Name:data:200",
        "Salary Component:Link/Salary Component:100",
        "Amount:Float:150",
        "Date:Date:200",
        "Active:Check:75",
        "Status:Data:100",
        "Remarks:Small Text:200",
    ]
