# Copyright 2023-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "version": "16.0.1.0.4",
    "name": "Mail with CC and TO text fields",
    "depends": ["mail", "mass_mailing"],
    "author": """
        Som It Cooperatiu SCCL,
        Som Connexió SCCL,
        Odoo Community Association (OCA)
    """,
    "category": "Auth",
    "website": "https://gitlab.com/somitcoop/erp-research/odoo-helpdesk",
    "license": "AGPL-3",
    "summary": """
        Mail with CC and TO text fields without res_partner model dependency".
    """,
    "data": [
        "wizard/mail_compose_message_view.xml",
    ],
    "demo": [],
    "application": True,
    "installable": True,
}
