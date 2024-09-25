{
    # App information
    'name': "Odoo Kaneen",
    'version': '15.0.0.0',
    'category': 'Sales',
    'author': 'LBS Company',

    # Dependencies
    'depends': ['sale_management', 'account', 'product_multiple_barcodes', 'stock_barcode', 'stock',
                'account_bank_statement_import'],
    # Views
    'data': [
        'data/email_template.xml',
        'data/ir.cron.xml',
        'data/mail_template_data.xml',
        'data/report_paperformat.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/product_template_view.xml',
        'views/purchase_order_view.xml',
        'views/res_config_settings_view.xml',
        'views/product_quality_comment_views.xml',
        'views/damaged_item_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_picking_views.xml',
        'views/res_partner_views.xml',
        'views/menuitem.xml',
        'views/res_company_view.xml',
        'views/picking_type_views.xml',
        'wizard/improt_product_view.xml',
        'wizard/stock_return_picking.xml',
        'wizard/return_wizard_view.xml',
        'wizard/return_wizard_validation_view.xml',
        'report/lbs_invoice_custom_report_template.xml',
        'data/mail_template_invoice.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'mo_kaneen/static/src/js/lazy_barcode_cache.js',
            'mo_kaneen/static/src/models/message/message.js',
        ],
        'web.assets_qweb': [
            'mo_kaneen/static/src/components/message/message.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,
}
