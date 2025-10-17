# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "widget_list_message",
    "version": "16.0.1.0.2",
    "depends": [
        "web",
    ],
    "author": """
        Som It Cooperatiu SCCL,
        Som Connexió SCCL,
        Odoo Community Association (OCA)
    """,
    "category": "web",
    "website": "https://gitlab.com/somitcoop/erp-research/odoo-helpdesk",
    "license": "AGPL-3",
    "summary": """
        SomItCoop ODOO widget to set limit columns on list view.
    """,
    "data": [],
    "assets": {
        "web.assets_backend": [
            "widget_list_message/static/src/js/*.js",
            "widget_list_message/static/src/css/*.css",
            "widget_list_message/static/src/xml/*.xml",
        ],
    },
    "qweb": [],
    "application": False,
    "installable": True,
}
