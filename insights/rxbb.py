"""RxBB customizations: user-level restriction flag for the Insights UI."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

USER_FIELDS = {
    "User": [
        {
            "fieldname": "insights_restricted_user",
            "label": "Insights Restricted User",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "enabled",
            "description": (
                "When checked, this user sees only the Dashboards tab in RxBB Insights "
                "(Workbooks, Data Sources, Data Store and Settings are hidden)."
            ),
        },
    ]
}


def ensure_rxbb_user_fields() -> None:
    create_custom_fields(USER_FIELDS, update=True)
