{
    # App information
    'name': "Odoo Shiprocket Integration",
    'version': '15.0.0.0',
    'category': 'Inventory/Delivery',
    'author': 'LBS Company',

    # Dependencies
    'depends': ['sale_management', 'stock'],
    # Views
    'data': [
        'data/shiprocket_data.xml',
        'views/sale_order_views.xml'
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
