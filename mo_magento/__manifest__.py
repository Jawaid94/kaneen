{
    # App information
    'name': "Odoo Magento",
    'version': '15.0.0.0',
    'category': 'Sales',
    'author': 'LBS Company',

    # Dependencies
    'depends': ['odoo_magento2_ept'],
    # Views
    'data': [
        'security/ir.model.access.csv',
        'data/ir.cron.xml',
        'views/product_template_view.xml',
        'views/magento_instance_view.xml',
        'wizard/set_availavle_in_magento_view.xml'

    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
