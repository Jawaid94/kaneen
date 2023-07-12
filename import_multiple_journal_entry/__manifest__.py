# -*- coding: utf-8 -*-
{
    'name': 'Import Multiple Journal Entries from CSV File in Odoo',
    'version': '15.0.0.1',
    'sequence': 4,
    'category': 'Accounting',
    'summary': '',
    'description': """
	""",
    'author': 'Jawaid Iqbal',
    'website': 'https://www.linkedin.com/in/muhammad-jawaid-iqbal-659a6898/',
    'depends': ['base', 'sale_management', 'account', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move.xml'
    ],
    'qweb': [
    ],
    'demo': [],
    'license': 'OPL-1',
    'test': [],
    'installable': True,
    'auto_install': False,
    "images": ['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
