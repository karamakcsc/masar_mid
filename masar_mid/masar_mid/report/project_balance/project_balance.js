// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Project Balance"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
		},
		{
			fieldname: "account",
			label: "Account",
			fieldtype: "MultiSelectList",
			options: "Account",
			get_data: function(txt) {
				return frappe.db.get_link_options("Account", txt);
			}
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Link",
			options: "Party Type",
			default: "Customer",
		},
		{
			fieldname: "party",
			label: __("Party"),
			fieldtype: "Dynamic Link",
			get_options: function () {
				var party_type = frappe.query_report.get_filter_value("party_type");
				var party = frappe.query_report.get_filter_value("party");
				if (party && !party_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return party_type;
			},
		}
	]
};
