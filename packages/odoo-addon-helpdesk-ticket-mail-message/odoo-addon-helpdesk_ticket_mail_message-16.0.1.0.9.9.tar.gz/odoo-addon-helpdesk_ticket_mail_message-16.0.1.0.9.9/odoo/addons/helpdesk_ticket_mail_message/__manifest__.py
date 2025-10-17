# Copyright 2024-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SomItCoop Odoo helpdesk ticket mail message",
    "version": "16.0.1.0.9",
    "depends": [
        "helpdesk_mgmt",
        "web",
        "widget_list_row_color",
        "widget_list_limit_cell",
        "mail_cc_and_to_text",
        "widget_list_message",
        "mail_tracking",
    ],
    "author": """
        Som It Cooperatiu SCCL,
        Som Connexió SCCL,
        Odoo Community Association (OCA)
    """,
    "category": "Tools",
    "website": "https://gitlab.com/somitcoop/erp-research/odoo-helpdesk",
    "license": "AGPL-3",
    "summary": "Helpdesk Ticket Mail Message",
    "description": """
        Allows sending an email from the ticket from a new tab where
        the email communications and notes associated with the ticket
        are recorded have been added.
    """,
    "data": [
        "data/helpdesk_data.xml",
        "views/helpdesk_ticket_view.xml",
        "views/mail_template_view.xml",
        "views/helpdesk_ticket_team_view.xml",
        "wizard/mail_compose_message_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "helpdesk_ticket_mail_message/static/src/js/*.js",
            "helpdesk_ticket_mail_message/static/src/css/*.css",
        ],
    },
    "application": False,
    "installable": True,
    "post_init_hook": "post_install_hook",
}
