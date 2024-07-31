# Part of Softhealer Technologies.
{
    "name": "Trello-Odoo Connector | Odoo Trello Integration",

    "author": "Softhealer Technologies",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "15.0.1",

    "license": "OPL-1",

    "category": "Extra Tools",

    "summary": "Trello Odoo Integration, Filter Trello Data Module, Sync Trello Data, Fetch Trello Code In Odoo,Rest API Trello,Trello Project Management,Trello Odoo Sync,Odoo Trello Connector,Trello Odoo,By-directional sync between Trello & Odoo,Odoo ERP To Trello",

    "description": """Trello is a project management and team collaboration tool. Trello has a similar appearance to a board with sticky notes - projects and tasks can be organized into columns and moved around easily to indicate workflow, project ownership, and status. This app will provide a facility to import and export your trello project and task with odoo.""",
    'depends': ['base_setup', 'project', 'sh_project_stages'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sh_trello_creds.xml',
        'views/sh_trello_logger.xml',
        'views/sh_tasks.xml',
        'views/sh_create_project.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'sh_trello_connector/static/src/js/sh_ref_button.js',
        ],
        'web.assets_qweb': [
            'sh_trello_connector/static/src/xml/sh_refresh_button.xml'
        ]
    },
    'demo': [],
    'installation': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/background.png', ],
    "price": 65,
    "currency": "EUR"
}
