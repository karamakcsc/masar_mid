frappe.query_reports["Left Employees Payment Summary"] = {
    filters: [
        {
            fieldname: "summary_type",
            label: "Summary Type",
            fieldtype: "Select",
            options: ["Yearly", "Monthly"],
            default: "Yearly",
            reqd: 1
        },
        {
            fieldname: "year",
            label: "Year",
            fieldtype: "Int",
            default: new Date().getFullYear()
        },
        {
            fieldname: "from_date",
            label: "From Relieving Date",
            fieldtype: "Date"
        },
        {
            fieldname: "to_date",
            label: "To Relieving Date",
            fieldtype: "Date"
        },
		{
			fieldname: "employee",
			label: "Employee",
			fieldtype: "Link",
			options: "Employee"
		},
        {
            fieldname: "department",
            label: "Department",
            fieldtype: "Link",
            options: "Department"
        },
		{
			fieldname: "designation",
			label: "Designation",
            fieldtype: "Link",
            options: "Designation"
		}
    ]
};
