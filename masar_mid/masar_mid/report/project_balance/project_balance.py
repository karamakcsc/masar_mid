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
    conditions = ["tge.is_cancelled = 0"]
    params = {}

    if filters.get("project"):
        conditions.append("tge.project = %(project)s")
        params["project"] = filters.get("project")

    if filters.get("from_date") and filters.get("to_date"):
        if filters.get("from_date") <= filters.get("to_date"):
            conditions.append("tge.posting_date BETWEEN %(from_date)s AND %(to_date)s")
            params["from_date"] = filters.get("from_date")
            params["to_date"] = filters.get("to_date")
        else:
            frappe.throw("From Date must be less than or equal to To Date")
    else:
        frappe.throw("Please select both From Date and To Date")

    if filters.get("party_type"):
        conditions.append("tge.party_type = %(party_type)s")
        params["party_type"] = filters.get("party_type")
    if filters.get("party"):
        conditions.append("tge.party = %(party)s")
        params["party"] = filters.get("party")

    account_list = []
    if filters.get("account"):
        if isinstance(filters.get("account"), str):
            account_list = [a.strip() for a in filters.get("account").split(",") if a.strip()]
        else:
            account_list = filters.get("account")

        if account_list:
            placeholders = ", ".join([f"%(acc_{i})s" for i in range(len(account_list))])
            conditions.append(f"tge.account IN ({placeholders})")
            for i, acc in enumerate(account_list):
                params[f"acc_{i}"] = acc

    where_clause = "WHERE " + " AND ".join(conditions)

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

    data = frappe.db.sql(query, params, as_dict=True)
    return data
