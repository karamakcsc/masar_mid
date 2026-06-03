from . import __version__ as app_version

app_name = "masar_mid"
app_title = "Masar MID"
app_publisher = "KCSC"
app_description = "Masar MID"
app_email = "info@kcsc.com.jo"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/masar_mid/css/masar_mid.css"
# app_include_js = "/assets/masar_mid/js/masar_mid.js"

# include js, css files in header of web template
# web_include_css = "/assets/masar_mid/css/masar_mid.css"
# web_include_js = "/assets/masar_mid/js/masar_mid.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "masar_mid/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "masar_mid.utils.jinja_methods",
#	"filters": "masar_mid.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "masar_mid.install.before_install"
# after_install = "masar_mid.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "masar_mid.uninstall.before_uninstall"
# after_uninstall = "masar_mid.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "masar_mid.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }
# Document Events
# ---------------
# Hook on document methods and events
# doc_events = {
#     "*": {
#         "method": "",
#     }
# }

doctype_js = {
    "Employee": "custom/employee/employee.js",
    "Salary Component": "custom/salary_component/salary_component.js",
    "Payment Entry": "custom/payment_entry/payment_entry.js"
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"masar_mid.tasks.all"
#	],
#	"daily": [
#		"masar_mid.tasks.daily"
#	],
#	"hourly": [
#		"masar_mid.tasks.hourly"
#	],
#	"weekly": [
#		"masar_mid.tasks.weekly"
#	],
#	"monthly": [
#		"masar_mid.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "masar_mid.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "masar_mid.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "masar_mid.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"masar_mid.auth.validate"
# ]
     
fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "name", "in", [
                # Department
                "Department-custom_section_break_irx5i",
                "Department-custom_ss_budget_element",
                "Department-custom_ss_cost_center",
                "Department-custom_column_break_yfiga",
                "Department-custom_ss_project"
                # Salary Component
                "Salary Component-custom_formula_check", 
                # Company
                "Company-custom_section_break_9o0od" , 
                "Company-custom_social_security_liabilities", 
                "Company-employee_share_rate", 
                "Company-company_share_rate",
                "Company-column_break_25",
                "Company-section_break_23",
                "Company-custom_social_security_expenses",
                "Company-custom_company_share_rate_dangerous",
                # Cheque
                "Cheque-custom_cheque_memo"
                # Employee 
                "Employee-custom_salary_component_table",
                "Employee-custom_salary_components", 
                "Employee-social_security_amount", 
                "Employee-social_security_salary",
                "Employee-social_security_date",
                "Employee-column_break_65",
                "Employee-tax_type",
                "Employee-employee_share_rate",
                "Employee-social_security_number",
                "Employee-custom_is_hazard",
                "Employee-is_social_security_applicable",
                "Employee-social_security_details"
            ]
        ]
    ]},{
        "doctype": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                    # Cheque
                    "Cheque-main-field_order",
                    "Cheque-cheque_no-in_preview",
                    "Cheque-cheque_no-in_standard_filter",
                    "Cheque-cheque_no-in_global_search",
                    "Cheque-cheque_amount-precision",
                    "Cheque-alternative_party_name-allow_on_submit",
                    # Asset 
                    "Asset-naming_series-default",
                    "Asset-naming_series-options",
                    "Asset-main-field_order"
                ]]
                ]}
]
