# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


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
    cond = ["tge.is_cancelled = 0"]
    if filters.get("project"):
        cond.append("tge.project = %(project)s")
    if filters.get("from_date") and filters.get("to_date"):
        if filters.get("from_date") <= filters.get("to_date"):
            cond.append("tge.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        else:
            frappe.throw("From Date must be less than or equal to To Date")
    else:
        frappe.throw("Please select both From Date and To Date")
    if filters.get("party_type"):
        cond.append("tge.party_type = %(party_type)s")
    if filters.get("party"):
        cond.append("tge.party = %(party)s")
    if filters.get("account"):
        if isinstance(filters.get("account"), str):
            accounts = [a.strip() for a in filters.get("account").split(",") if a.strip()]
        else:
            accounts = filters.get("account")
        cond.append(f"tge.account IN ({', '.join(['%s'] * len(accounts))})")
    else:
        accounts = []
    where_clause = "WHERE " + " AND ".join(cond)
    query = f"""
        SELECT
            tge.account AS account,
            tge.project AS project,
            SUM(tge.debit) AS debit,
            SUM(tge.credit) AS credit,
            SUM(tge.debit - tge.credit) AS balance
        FROM `tabGL Entry` tge
        {where_clause}
        GROUP BY tge.account, tge.project
        ORDER BY tge.account
    """
    params = filters.copy()
    if accounts:
        if isinstance(params, dict):
            params = list(accounts)
        else:
            params.extend(accounts)

    data = frappe.db.sql(query, params, as_dict=True)
    return data
