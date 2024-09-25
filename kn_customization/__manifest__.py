{
    'name': 'kaneen Additional Customization',
    'version': '1.2',
    'summary': 'This module contains all the additional customization related to kaneen process',
    'sequence': 10,
    'description': """""",
    'author': 'Odoo Developer',
    'category': 'Customization',
    'website': '',
    'depends': ['base', 'stock', 'sale', 'purchase', 'report_xlsx','odoo_magento2_ept','helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/user_groups.xml',
        # 'views/product_template.xml',
        # 'views/stock_picking.xml',
        'views/menus.xml',
        'views/sale_order.xml',
        'views/helpdesk_ticket.xml',
        # 'reports/report.xml',

    ],
    'license': 'LGPL-3',
}
