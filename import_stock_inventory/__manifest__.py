# -*- coding: utf-8 -*-

{
    # Product Info
    'name': 'Import Stock Inventory Adjustment From CSV',
    'category': 'stock',
    'version': '15.0.0.1',
    'license': 'OPL-1',
    'sequence': 1,
    'summary': 'Import Stock Inventory Adjustment Which Help You To Adjust Your Inventory Adjustments With In Few Minutes. You Can Prepare The CSV File For The Import Time.',

    # Writer
    'author': 'Jawaid Iqbal',
    'website': 'https://www.linkedin.com/in/muhammad-jawaid-iqbal-659a6898/',

    # Dependencies
    'depends': ['stock'],

    # Views
    'data': ['security/ywt_import_stock_inventory_security.xml',
             'security/ir.model.access.csv',
             'data/stock_invenotry_seq.xml',
             'view/main_menu.xml',
             'wizard_view/ywt_import_stock_inventory_views.xml',
             'view/ywt_import_stock_inventory_log_views.xml'],

    # Banner     
    "images": ["static/description/banner.png"],

    # Technical 
    'installable': True,
    'auto_install': False,
    'application': True,

    'description': """
        Import Stock from CSV file.
        Import Stock inventory from CSV File.
        Import Inventory Adjustment, stock import from CSV,Inventory adjustment import
       
         
    
    """

}
