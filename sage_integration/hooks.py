from . import __version__ as app_version

app_name = "sage_integration"
app_title = "Sage Integration"
app_publisher = "Richard"
app_description = "All intéegration with Sage X3"
app_email = "dodziamouzou@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sage_integration/css/sage_integration.css"
# app_include_js = "/assets/sage_integration/js/sage_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/sage_integration/css/sage_integration.css"
# web_include_js = "/assets/sage_integration/js/sage_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sage_integration/public/scss/website"

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
#	"methods": "sage_integration.utils.jinja_methods",
#	"filters": "sage_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sage_integration.install.before_install"
# after_install = "sage_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sage_integration.uninstall.before_uninstall"
# after_uninstall = "sage_integration.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sage_integration.notifications.get_notification_config"

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

override_doctype_class = {
	"Material Request": "sage_integration.overrides.materiel_request.CustomMaterialRequest",
    "Stock Entry": "sage_integration.overrides.stock_entry.CustomStockEntry",
    "Stock Reconciliation": "sage_integration.overrides.stock_reconciliation.CustomStockStockReconciliation",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
   "cron": {
       "* * * * *": [
           "sage_integration.tasks.cron"
       ],
    },
	"all": [
		"sage_integration.tasks.all"
	],
	"daily": [
		"sage_integration.tasks.daily"
	],
	"hourly": [
		"sage_integration.tasks.hourly"
	],
	"weekly": [
		"sage_integration.tasks.weekly"
	],
	"monthly": [
		"sage_integration.tasks.monthly"
	],
}

# Testing
# -------

# before_tests = "sage_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "sage_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "sage_integration.task.get_dashboard_data"
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
#	"sage_integration.auth.validate"
# ]
fixtures = [
    "Custom Field",
    "Client Script",
    #"Server Script",
    {"dt": "Server Script", "filters": [["disabled", "=", 0]]},
]
