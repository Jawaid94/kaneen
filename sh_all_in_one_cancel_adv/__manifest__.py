# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
{
    "name": "All In One Cancel - Advance | Cancel Sale Orders | Cancel Purchase Orders | Cancel Invoices | Cancel Inventory",
    "author": "Jawaid Iqbal",
    "website": "https://www.linkedin.com/in/muhammad-jawaid-iqbal-659a6898/",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Sale Order Cancel, Cancel Quotation, Purchase Order Cancel, Request For Quotation Cancel, Delete Invoice, Cancel Payment, Cancel Stock Picking,Cancel Stock Moves Odoo",
    "description": """This module helps to cancel sale orders, purchase orders, invoices, payments, inventory (inventory transfer,stock move), HR Expenses, point of sale orders. You can also cancel multiple records from the tree view.""",
    "version": "15.0.4",
    "depends": [

        "purchase", "sale_management", "stock"
    ],
    "application": True,
    "data": [

        "sh_account_cancel/security/account_security.xml",
        "sh_account_cancel/data/data.xml",
        "sh_account_cancel/views/res_config_settings.xml",
        "sh_account_cancel/views/views.xml",

        'sh_purchase_cancel/security/purchase_security.xml',
        'sh_purchase_cancel/data/data.xml',
        'sh_purchase_cancel/views/purchase_config_settings.xml',
        'sh_purchase_cancel/views/views.xml',

        'sh_sale_cancel/security/sale_security.xml',
        'sh_sale_cancel/data/data.xml',
        'sh_sale_cancel/views/sale_config_settings.xml',
        'sh_sale_cancel/views/views.xml',

        'sh_stock_cancel/security/stock_security.xml',
        'sh_stock_cancel/data/data.xml',
        'sh_stock_cancel/views/res_config_settings.xml',
        'sh_stock_cancel/views/views.xml',

    ],

    "auto_install": False,
    "installable": True
}