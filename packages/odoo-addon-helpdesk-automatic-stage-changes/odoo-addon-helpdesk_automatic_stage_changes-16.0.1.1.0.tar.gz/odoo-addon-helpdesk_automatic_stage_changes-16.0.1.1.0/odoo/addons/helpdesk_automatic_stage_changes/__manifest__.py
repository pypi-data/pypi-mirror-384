# Copyright 2024-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "SomItCoop Odoo helpdesk automatic stage changes",
    "version": "16.0.1.1.0",
    "depends": [
        "helpdesk_ticket_mail_message",
    ],
    "author": """
        Som It Cooperatiu SCCL,
        Som Connexió SCCL,
        Odoo Community Association (OCA)
    """,
    "category": "Auth",
    "website": "https://gitlab.com/somitcoop/erp-research/odoo-helpdesk",
    "license": "AGPL-3",
    "summary": "Helpdesk automatic stage changes",
    "description": """
        Allows the configuration of the stages of a ticket. Customization of colors by
        stages and automatic stage changes when receiving or sending a message.
        The tickets will have customized colors according to the stage in the tree view.
    """,
    "data": [
        "views/helpdesk_ticket_stage_view.xml",
        "views/helpdesk_ticket_view.xml",
        "wizard/mail_compose_message_view.xml",
    ],
    "application": False,
    "installable": True,
}
