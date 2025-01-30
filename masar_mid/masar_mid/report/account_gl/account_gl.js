// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Account GL"] = {
	"filters": [

		{
			"fieldname": "account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account"
		},
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            // "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            // "reqd": 1,
            // "width": "60px"
        },

        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            // "default": frappe.datetime.get_today(),
            // "reqd": 1,
            // "width": "60px"
        }

	]
};
