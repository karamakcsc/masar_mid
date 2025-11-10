# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Sum

def execute(filters=None):
    columns = get_columns()
    data_rows = get_data(filters)
    return columns, data_rows


def get_columns():
    return [
        {"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Account", "width": 200},
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": "Debit", "fieldname": "debit", "fieldtype": "Currency", "width": 150},
        {"label": "Credit", "fieldname": "credit", "fieldtype": "Currency", "width": 150},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 150},
    ]

def get_data(filters=None):
    filters = filters or {}
    gl_entry = frappe.qb.DocType("GL Entry")
    
    query = (
        frappe.qb.from_(gl_entry)
        .select(
            gl_entry.account,
            gl_entry.project,
            Sum(gl_entry.debit).as_("debit"),
            Sum(gl_entry.credit).as_("credit"),
            (Sum(gl_entry.debit) - Sum(gl_entry.credit)).as_("balance")
        )
        .where(gl_entry.is_cancelled == 0)
        .groupby(gl_entry.account, gl_entry.project)
        .orderby(gl_entry.account)
    )
    if filters.get("project"):
        query = query.where(gl_entry.project == filters.get("project"))
    if filters.get("from_date") and filters.get("to_date"):
        if filters.get("from_date") <= filters.get("to_date"):
            query = query.where(
                gl_entry.posting_date[filters.get("from_date"):filters.get("to_date")]
            )
        else:
            frappe.throw("From Date must be less than or equal to To Date")
    else:
        frappe.throw("Please select both From Date and To Date")
    if filters.get("party_type"):
        query = query.where(gl_entry.party_type == filters.get("party_type"))
    if filters.get("party"):
        query = query.where(gl_entry.party == filters.get("party"))
    if filters.get("account"):
        account_list = []
        if isinstance(filters.get("account"), str):
            account_list = [a.strip() for a in filters.get("account").split(",") if a.strip()]
        else:
            account_list = filters.get("account")
        
        if account_list:
            query = query.where(gl_entry.account.isin(account_list))
    frappe.throw(str(query))
    data = query.run(as_dict=True)
    return data