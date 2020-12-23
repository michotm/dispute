# Copyright 2020 Pharmasimple (https://www.pharmasimple.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Disputes',
    'category': 'Dispute',
    'summary': 'disputes',
    'version': '14.0.1.0.0',
    'description': """
    - Base module for disputes management
    """,
    'author': "Pharmasimple",
    'license': "AGPL-3",
    'website': "https://www.pharmasimple.fr",
    'depends': [
        "mail",
        "product",
    ],
    'data': ['data/dispute.xml',
            # 'demo/demo_dispute.xml',
            'report/dispute_reports.xml',
            'report/dispute_templates.xml',
            'data/mail_template_data.xml',
            'security/dispute_security.xml',
            'security/ir.model.access.csv',
            'views/dispute.xml',
            'views/res_partner_views.xml',
            ],
    'installable': True,
    'application': False,
}
