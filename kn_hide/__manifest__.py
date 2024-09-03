{
    'name': "Hide Data",
    'summary': """
        Restrict Menu Items from Specific Users""",
    'description': """
        Restrict Menu Items from Specific Users""",
    'author': 'Odoo Developer',
    'images': ["static/description/banner.png"],
    'category': 'Customization',
    'version': "15.0",
    'license': 'AGPL-3',
    'depends': [
        'base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'security/record_rules.xml',
        'views/user_roles.xml',
        'views/res_users.xml',
             ],
    'module_type': 'official',
}
