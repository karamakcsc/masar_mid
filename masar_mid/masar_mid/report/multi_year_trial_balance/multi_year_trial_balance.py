# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, cstr, flt, getdate

import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
	get_dimension_with_children,
)
from erpnext.accounts.report.financial_statements import (
	filter_accounts,
	get_cost_centers_with_children,
	set_gl_entries_by_account,
)
from erpnext.accounts.report.utils import convert_to_presentation_currency, get_currency
from erpnext.accounts.utils import get_zero_cutoff

value_fields = ("opening_debit", "opening_credit", "debit", "credit", "closing_debit", "closing_credit")


def execute(filters=None):
	validate_filters(filters)
	periods = get_fiscal_year_periods(filters.from_date, filters.to_date, filters.company)
	if not periods:
		frappe.throw(_("No fiscal years found in the given date range"))

	accounts = get_accounts(filters.company)
	if not accounts:
		return [], []

	# filter_accounts adds 'indent' and sorts by lft
	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
	company_currency = filters.presentation_currency or erpnext.get_company_currency(filters.company)

	# Store period-wise balances for each account
	period_balances = {}
	for period in periods:
		period_balances[period["label"]] = get_period_balances(
			accounts, filters, period["start_date"], period["end_date"], company_currency
		)

	# Combine into rows, one per account
	data = build_data_rows(
		accounts,
		accounts_by_name,
		periods,
		period_balances,
		filters,
		company_currency,
	)

	columns = get_columns(periods)
	return columns, data


def validate_filters(filters):
	if not filters.company:
		frappe.throw(_("Company is required"))

	if not filters.from_date or not filters.to_date:
		frappe.throw(_("From Date and To Date are required"))

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))


def get_fiscal_year_periods(from_date, to_date, company):
	"""Return list of fiscal year periods that intersect the given date range."""
	fiscal_years = frappe.db.sql(
		"""
		SELECT name, year_start_date, year_end_date
		FROM `tabFiscal Year`
		WHERE year_start_date <= %s
			AND year_end_date >= %s
		ORDER BY year_start_date
	""",
		( to_date, from_date),
		as_dict=1,
	)

	periods = []
	for fy in fiscal_years:
		period_start = max(from_date, fy.year_start_date)
		period_end = min(to_date, fy.year_end_date)
		if period_start <= period_end:
			periods.append(
				{
					"label": fy.name,
					"start_date": period_start,
					"end_date": period_end,
				}
			)
	return periods


def get_accounts(company):
	return frappe.db.sql(
		"""
		SELECT name, account_number, parent_account, account_name,
			root_type, report_type, is_group, lft, rgt
		FROM `tabAccount`
		WHERE company = %s
		ORDER BY lft
	""",
		company,
		as_dict=1,
	)


def get_period_balances(accounts, filters, period_start, period_end, company_currency):
	"""Compute opening, debit, credit, closing for each account for a single period."""
	period_filters = frappe._dict(filters.copy())
	period_filters.from_date = period_start
	period_filters.to_date = period_end

	ignore_is_opening = frappe.db.get_single_value("Accounts Settings", "ignore_is_opening_check_for_reporting")

	opening_balances = get_opening_balances(period_filters, ignore_is_opening)

	gl_entries_by_account = {}
	set_gl_entries_by_account(
		period_filters.company,
		period_filters.from_date,
		period_filters.to_date,
		period_filters,
		gl_entries_by_account,
		root_lft=None,
		root_rgt=None,
		ignore_closing_entries=not flt(period_filters.with_period_closing_entry_for_current_period),
		ignore_opening_entries=True,
		group_by_account=True,
	)

	result = {}
	for d in accounts:
		opening_debit = opening_balances.get(d.name, {}).get("opening_debit", 0.0)
		opening_credit = opening_balances.get(d.name, {}).get("opening_credit", 0.0)
		debit = 0.0
		credit = 0.0
		for entry in gl_entries_by_account.get(d.name, []):
			if cstr(entry.is_opening) != "Yes" or ignore_is_opening:
				debit += flt(entry.debit)
				credit += flt(entry.credit)

		closing_debit = opening_debit + debit
		closing_credit = opening_credit + credit

		if period_filters.get("show_net_values"):
			prepare_opening_closing_for_row(d, opening_debit, opening_credit, closing_debit, closing_credit)
			opening_debit, opening_credit = d.get("opening_debit", 0), d.get("opening_credit", 0)
			closing_debit, closing_credit = d.get("closing_debit", 0), d.get("closing_credit", 0)

		result[d.name] = {
			"opening_debit": opening_debit,
			"opening_credit": opening_credit,
			"debit": debit,
			"credit": credit,
			"closing_debit": closing_debit,
			"closing_credit": closing_credit,
		}

	return result


def get_opening_balances(filters, ignore_is_opening):
	balance_sheet_opening = get_rootwise_opening_balances(filters, "Balance Sheet", ignore_is_opening)
	pl_opening = get_rootwise_opening_balances(filters, "Profit and Loss", ignore_is_opening)
	balance_sheet_opening.update(pl_opening)
	return balance_sheet_opening


def get_rootwise_opening_balances(filters, report_type, ignore_is_opening):
	gle = []
	last_period_closing_voucher = ""
	ignore_closing_balances = frappe.db.get_single_value("Accounts Settings", "ignore_account_closing_balance")

	if not ignore_closing_balances:
		last_period_closing_voucher = frappe.db.get_all(
			"Period Closing Voucher",
			filters={
				"docstatus": 1,
				"company": filters.company,
				"period_end_date": ("<", filters.from_date),
			},
			fields=["period_end_date", "name"],
			order_by="period_end_date desc",
			limit=1,
		)

	accounting_dimensions = get_accounting_dimensions(as_list=False)

	if last_period_closing_voucher:
		gle = get_opening_balance_from_closing_balance(
			filters,
			report_type,
			accounting_dimensions,
			period_closing_voucher=last_period_closing_voucher[0].name,
			ignore_is_opening=ignore_is_opening,
		)

		if getdate(last_period_closing_voucher[0].period_end_date) < getdate(add_days(filters.from_date, -1)):
			start_date = add_days(last_period_closing_voucher[0].period_end_date, 1)
			gle += get_opening_balance_from_gl(
				filters, report_type, accounting_dimensions, start_date=start_date, ignore_is_opening=ignore_is_opening
			)
	else:
		gle = get_opening_balance_from_gl(
			filters, report_type, accounting_dimensions, ignore_is_opening=ignore_is_opening
		)

	opening = frappe._dict()
	for d in gle:
		opening.setdefault(
			d.account,
			{
				"account": d.account,
				"opening_debit": 0.0,
				"opening_credit": 0.0,
			},
		)
		opening[d.account]["opening_debit"] += flt(d.debit)
		opening[d.account]["opening_credit"] += flt(d.credit)

	return opening


def get_opening_balance_from_closing_balance(
	filters, report_type, accounting_dimensions, period_closing_voucher, ignore_is_opening
):
	closing_balance = frappe.qb.DocType("Account Closing Balance")
	accounts = frappe.db.get_all("Account", filters={"report_type": report_type}, pluck="name")

	opening_balance = (
		frappe.qb.from_(closing_balance)
		.select(
			closing_balance.account,
			closing_balance.account_currency,
			Sum(closing_balance.debit).as_("debit"),
			Sum(closing_balance.credit).as_("credit"),
			Sum(closing_balance.debit_in_account_currency).as_("debit_in_account_currency"),
			Sum(closing_balance.credit_in_account_currency).as_("credit_in_account_currency"),
		)
		.where((closing_balance.company == filters.company) & (closing_balance.account.isin(accounts)))
		.where(closing_balance.period_closing_voucher == period_closing_voucher)
		.groupby(closing_balance.account)
	)

	if not flt(filters.with_period_closing_entry_for_opening):
		opening_balance = opening_balance.where(closing_balance.is_period_closing_voucher_entry == 0)

	return apply_common_filters(opening_balance, filters, accounting_dimensions).run(as_dict=1)


def get_opening_balance_from_gl(filters, report_type, accounting_dimensions, start_date=None, ignore_is_opening=0):
	gl = frappe.qb.DocType("GL Entry")
	accounts = frappe.db.get_all("Account", filters={"report_type": report_type}, pluck="name")

	opening_balance = (
		frappe.qb.from_(gl)
		.select(
			gl.account,
			gl.account_currency,
			Sum(gl.debit).as_("debit"),
			Sum(gl.credit).as_("credit"),
			Sum(gl.debit_in_account_currency).as_("debit_in_account_currency"),
			Sum(gl.credit_in_account_currency).as_("credit_in_account_currency"),
		)
		.where((gl.company == filters.company) & (gl.account.isin(accounts)))
		.where(gl.is_cancelled == 0)
		.groupby(gl.account)
	)

	if start_date:
		opening_balance = opening_balance.where(
			(gl.posting_date >= start_date) & (gl.posting_date < filters.from_date)
		)
		if not ignore_is_opening:
			opening_balance = opening_balance.where(gl.is_opening == "No")
	else:
		if not ignore_is_opening:
			opening_balance = opening_balance.where(
				(gl.posting_date < filters.from_date) | (gl.is_opening == "Yes")
			)
		else:
			opening_balance = opening_balance.where(gl.posting_date < filters.from_date)

	if (
		not filters.show_unclosed_fy_pl_balances
		and report_type == "Profit and Loss"
		and not start_date
	):
		fiscal_year = frappe.get_cached_value("Fiscal Year", filters.fiscal_year, "year_start_date")
		if fiscal_year:
			opening_balance = opening_balance.where(gl.posting_date >= fiscal_year)

	if not flt(filters.with_period_closing_entry_for_opening):
		opening_balance = opening_balance.where(gl.voucher_type != "Period Closing Voucher")

	return apply_common_filters(opening_balance, filters, accounting_dimensions).run(as_dict=1)


def apply_common_filters(query, filters, accounting_dimensions):
	if filters.cost_center:
		query = query.where(
			query.cost_center.isin(get_cost_centers_with_children(filters.get("cost_center")))
		)

	if filters.project:
		query = query.where(query.project.isin(filters.project))

	if frappe.db.count("Finance Book"):
		if filters.get("include_default_book_entries"):
			company_fb = frappe.get_cached_value("Company", filters.company, "default_finance_book")
			if filters.finance_book and company_fb and cstr(filters.finance_book) != cstr(company_fb):
				frappe.throw(_("To use a different finance book, please uncheck 'Include Default FB Entries'"))
			query = query.where(
				(query.finance_book.isin([cstr(filters.finance_book), cstr(company_fb), ""]))
				| (query.finance_book.isnull())
			)
		else:
			query = query.where(
				(query.finance_book.isin([cstr(filters.finance_book), ""])) | (query.finance_book.isnull())
			)

	if accounting_dimensions:
		for dimension in accounting_dimensions:
			if filters.get(dimension.fieldname):
				if frappe.get_cached_value("DocType", dimension.document_type, "is_tree"):
					filters[dimension.fieldname] = get_dimension_with_children(
						dimension.document_type, filters.get(dimension.fieldname)
					)
					query = query.where(query[dimension.fieldname].isin(filters[dimension.fieldname]))
				else:
					query = query.where(query[dimension.fieldname].isin(filters[dimension.fieldname]))

	if filters and filters.get("presentation_currency"):
		# conversion done later
		pass
	return query


def prepare_opening_closing_for_row(row, opening_debit, opening_credit, closing_debit, closing_credit):
	dr_or_cr = "debit" if row["root_type"] in ["Asset", "Equity", "Expense"] else "credit"
	reverse_dr_or_cr = "credit" if dr_or_cr == "debit" else "debit"

	valid = opening_debit if dr_or_cr == "debit" else opening_credit
	reverse = opening_credit if dr_or_cr == "debit" else opening_debit
	net = valid - reverse
	if net < 0:
		row["opening_debit"] = 0.0 if dr_or_cr == "debit" else abs(net)
		row["opening_credit"] = abs(net) if dr_or_cr == "debit" else 0.0
	else:
		row["opening_debit"] = net if dr_or_cr == "debit" else 0.0
		row["opening_credit"] = 0.0 if dr_or_cr == "debit" else net

	valid = closing_debit if dr_or_cr == "debit" else closing_credit
	reverse = closing_credit if dr_or_cr == "debit" else closing_debit
	net = valid - reverse
	if net < 0:
		row["closing_debit"] = 0.0 if dr_or_cr == "debit" else abs(net)
		row["closing_credit"] = abs(net) if dr_or_cr == "debit" else 0.0
	else:
		row["closing_debit"] = net if dr_or_cr == "debit" else 0.0
		row["closing_credit"] = 0.0 if dr_or_cr == "debit" else net


def build_data_rows(accounts, accounts_by_name, periods, period_balances, filters, company_currency):
	"""Build rows including all accounts (groups and leaves) with proper indent."""
	rows = []
	for acc in accounts:
		row = {
			"account": acc.name,
			"parent_account": acc.parent_account,
			"indent": acc.indent,          # critical for tree view
			"is_group_account": acc.is_group,
			"account_name": f"{acc.account_number} - {acc.account_name}" if acc.account_number else acc.account_name,
			"root_type": acc.root_type,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"currency": company_currency,
		}
		for period in periods:
			label = period["label"]
			vals = period_balances[label].get(acc.name, {})
			for field in value_fields:
				row[f"{field}_{label}"] = flt(vals.get(field, 0.0))
		rows.append(row)

	# Accumulate values from children to parents for each period
	for period in periods:
		label = period["label"]
		# Process in reverse order so children are processed before parents
		for row in reversed(rows):
			parent = row.get("parent_account")
			if parent and parent in accounts_by_name:
				parent_row = accounts_by_name[parent]
				# parent_row is a reference to the original account dict, but we need to update the row in `rows`
				# Actually `accounts_by_name` maps name -> account dict from the original `accounts` list.
				# We need to find the corresponding row in `rows`. Since rows are in same order as accounts,
				# we can use a dict for quick lookup.
				# Let's create a lookup dict for rows.
	# Better: create a lookup dict for rows
	row_by_name = {row["account"]: row for row in rows}
	for period in periods:
		label = period["label"]
		for row in reversed(rows):
			parent = row.get("parent_account")
			if parent and parent in row_by_name:
				parent_row = row_by_name[parent]
				for field in value_fields:
					parent_row[f"{field}_{label}"] = parent_row.get(f"{field}_{label}", 0.0) + row.get(f"{field}_{label}", 0.0)

	# Apply show_net_values to parent accounts after accumulation (if needed)
	if filters.get("show_net_values"):
		for row in rows:
			if row.get("is_group_account"):
				for period in periods:
					label = period["label"]
					opening_debit = row.get(f"opening_debit_{label}", 0.0)
					opening_credit = row.get(f"opening_credit_{label}", 0.0)
					closing_debit = row.get(f"closing_debit_{label}", 0.0)
					closing_credit = row.get(f"closing_credit_{label}", 0.0)
					prepare_opening_closing_for_row(row, opening_debit, opening_credit, closing_debit, closing_credit)
					# Update the row with netted values
					row[f"opening_debit_{label}"] = row.get("opening_debit", 0.0)
					row[f"opening_credit_{label}"] = row.get("opening_credit", 0.0)
					row[f"closing_debit_{label}"] = row.get("closing_debit", 0.0)
					row[f"closing_credit_{label}"] = row.get("closing_credit", 0.0)

	# Filter zero rows
	if not filters.get("show_zero_values"):
		rows = [r for r in rows if has_any_value(r, periods)]

	# Optionally hide group accounts (breaks tree, but respects filter)
	if not filters.get("show_group_accounts"):
		rows = [r for r in rows if not r.get("is_group_account")]

	# Total row: sum only top-level accounts (parent_account is None) if showing groups,
	# otherwise sum all rows.
	total_row = {
		"account": "'" + _("Total") + "'",
		"account_name": "'" + _("Total") + "'",
		"indent": 0,
		"has_value": True,
		"currency": company_currency,
	}
	for period in periods:
		label = period["label"]
		for field in value_fields:
			total_row[f"{field}_{label}"] = 0.0

	for r in rows:
		# If showing groups, include only top-level accounts (no parent)
		if filters.get("show_group_accounts") and r.get("parent_account"):
			continue
		for period in periods:
			label = period["label"]
			for field in value_fields:
				total_row[f"{field}_{label}"] += r.get(f"{field}_{label}", 0.0)

	rows.append({})
	rows.append(total_row)

	return rows


def has_any_value(row, periods):
	for period in periods:
		label = period["label"]
		for field in value_fields:
			if abs(row.get(f"{field}_{label}", 0.0)) >= get_zero_cutoff(row.get("currency", "USD")):
				return True
	return False


def get_columns(periods):
	columns = [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
	]
	for period in periods:
		label = period["label"]
		columns.extend([
			{"fieldname": f"opening_debit_{label}", "label": _(f"{label} Opening (Dr)"), "fieldtype": "Currency", "options": "currency", "width": 120},
			{"fieldname": f"opening_credit_{label}", "label": _(f"{label} Opening (Cr)"), "fieldtype": "Currency", "options": "currency", "width": 120},
			{"fieldname": f"debit_{label}", "label": _(f"{label} Debit"), "fieldtype": "Currency", "options": "currency", "width": 120},
			{"fieldname": f"credit_{label}", "label": _(f"{label} Credit"), "fieldtype": "Currency", "options": "currency", "width": 120},
			{"fieldname": f"closing_debit_{label}", "label": _(f"{label} Closing (Dr)"), "fieldtype": "Currency", "options": "currency", "width": 120},
			{"fieldname": f"closing_credit_{label}", "label": _(f"{label} Closing (Cr)"), "fieldtype": "Currency", "options": "currency", "width": 120},
		])
	return columns