# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Mail Composer Email To Suggestions",
    "version": "16.0.1.0.0",
    "depends": ["web", "helpdesk_mgmt", "mail_cc_and_to_text"],
    "author": """
        Som It Cooperatiu SCCL,
        Som Connexió SCCL,
        Odoo Community Association (OCA)
    """,
    "category": "web",
    "website": "https://gitlab.com/somitcoop/erp-research/odoo-helpdesk",
    "license": "AGPL-3",
    "summary": """
        SomItCoop ODOO widget to add enhancements to the mail composer.
    """,
    "data": [
        "views/res_config_settings.xml",
        "wizards/mail_compose_message_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "widget_mail_composer_email_to/static/src/js/*.js",
            "widget_mail_composer_email_to/static/src/css/*.css",
            "widget_mail_composer_email_to/static/src/xml/*.xml",
        ],
    },
    "qweb": [],
    "application": False,
    "installable": True,
}
