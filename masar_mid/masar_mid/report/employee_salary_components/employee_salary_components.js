// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Salary Components"] = {
	"filters": [

		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},

		{
			"fieldname": "salary_component",
			"label": __("Salary Component"),
			"fieldtype": "Link",
			"options": "Salary Component"
		},

		{
			"fieldname": "esc_amount",
			"label": __("Amount"),
			"fieldtype": "Float",
		},

		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive\nSuspended\nLeft"
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
        },

		{
			"fieldname": "is_active",
			"label": __("Is Active"),
			"fieldtype": "Check",
		},
		

	]
};
