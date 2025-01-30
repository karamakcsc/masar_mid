# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    filters = filters or {}
    # validate_filters(filters)
    return columns(), data(filters), None

def validate_filters(filters):
    if not filters.get("account"):
        frappe.throw("Please specify an account.")
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw("Please specify both 'from_date' and 'to_date'.")

def data(filters):
    conditions = []
    parameters = {"account": filters.get("account")}

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("tge.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        parameters.update({
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date"),
        })

    if filters.get("account"):
        conditions.append("tge.account = %(account)s")

    # Join all conditions into a single string
    where_clause = ''
    if len(conditions) != 0:
        where_clause = " AND ".join(conditions)

    query = f"""
        SELECT 
            tge.posting_date, 
            tge.debit, 
            tge.credit, 
            (tge.debit - tge.credit) AS balance,
            SUM(tge.debit - tge.credit) OVER (ORDER BY tge.posting_date, tge.creation) AS accumulated_balance,
            tge.voucher_type, tge.voucher_no
        FROM `tabGL Entry` tge
        WHERE {where_clause}
    """
    
    return frappe.db.sql(query, parameters)

def columns():
    return [
        "Posting Date:Date:200",
        "Debit:Float:200",
        "Credit:Float:200",  # Fixed the typo
        "Balance:Float:200",
        "Accumulated Balance:Float:200",
        "Voucher Type:Data:200",
        "Voucher No:Data:200"
    ]
