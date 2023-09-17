# -*- coding: utf-8 -*-
{
    'name': "List View Manager",

    'summary': """
        This app will allow app to manage the List Views on the fly and endeavour a quick and effortless way to 
        view/manage the desired data, where you’ve multifarious options to slice and dice your List View easily
        on a click.
         """,

    'description': """
	List View ,
	Advance Search ,
	Read/Edit Mode ,
	Dynamic List ,
	Hide/Show list view columns ,
	List View Manager ,
	Odoo List View ,
	Odoo Advanced Search ,
	Odoo Connector ,
	Odoo Manage List View ,
	Drag and edit columns ,
	Dynamic List View Apps , 
	Advance Dynamic Tree View ,
	Dynamic Tree View Apps ,
	Advance Tree View Apps ,
	List/Tree View Apps ,
	Tree/List View Apps  ,
	Freeze List View Header ,
	List view Advance Search ,
	Tree view Advance Search ,
	Best List View Apps ,
	Best Tree View Apps ,
	Tree View Apps ,
	List View Apps ,
	List View Management Apps ,
	Treeview ,
	Listview ,
	Tree View ,
	one2many view, 
        list one2many view, 
        sticky header, 
        report templates, 
        sale order lists, 
        approval check lists, 
        pos order lists, 
        orders list in odoo,
        top app, 
        best app, 
        best apps
    """,
    'author': "Ksolves India Ltd.",
    'sequence': 1,
    'website': "https://www.ksolves.com/",
    'live_test_url': 'https://listview14.kappso.com/web/demo_login',
    'category': 'Tools',
    'version': '1.0.9',
    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'web'],
    # always loaded
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 118.0,
    'maintainer': 'Ksolves India Ltd.',
    'support': 'sales@ksolves.com',
    'images': ['static/description/LVM-V14-new.gif'],
    'assets': {
        'web.assets_backend': [
            'ks_list_view_manager/static/src/css/spectrum.css',
            'ks_list_view_manager/static/lib/spectrum/spectrum.js',
            'ks_list_view_manager/static/lib/stickytableheaders/jquery.stickytableheaders.js',
            'ks_list_view_manager/static/lib/resizableColumns/jQuery.ksResizableColumns.js',
            'ks_list_view_manager/static/src/css/ks_list_view_manager.scss',
            'ks_list_view_manager/static/src/js/ks_lvm_view.js',
            'ks_list_view_manager/static/src/js/ks_list_view_manager_controller.js',
            'ks_list_view_manager/static/src/js/ks_list_view_manager_renderer.js',
            'ks_list_view_manager/static/src/js/ks_color_picker.js',
            'ks_list_view_manager/static/src/js/ks_inventory_controller.js',
            'ks_list_view_manager/static/src/js/ks_account_conroller.js',
        ],
'web.assets_qweb': [
            'ks_list_view_manager/static/src/xml/**/*',
        ],
    },
    'data': [
        # 'views/ks_list_view_manager_assets.xml', -- not necessary to call in template, already added in manifest
        'views/ks_res_config_settings.xml',
        'security/ir.model.access.csv',
        'security/ks_security_groups.xml',
    ],

    'qweb': [
        'static/src/xml/ks_list_templates.xml',
        'static/src/xml/ks_advance_search.xml',
        'static/src/xml/ks_cancel_edit_template.xml',
        'static/src/xml/ks_lvm_button.xml',
    ],
    'post_init_hook': 'post_install_hook',
    'uninstall_hook': 'uninstall_hook',
}
