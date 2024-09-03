# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Auto Project Task Stages",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "license": "OPL-1",
    "version": "15.0.1",
    "category": "Project",
    "summary": """
        Define Stages In Project Task,Manage Project Phase,
        Maintain Project Stages With Task,Project Task Management Module,
        Handle Different Project Phases,
        Different Stages In Different Projects App Odoo
        """,
    "description": """
        Stages are the most important things in the project. 
        In this module, you can define project task wise stages. 
        You can create different project task stages
        for different projects.
        """,
    "depends": ["project"],
    "data": [
        'security/ir.model.access.csv',
        'views/sh_project_view.xml',
        'views/mass_project_update_action.xml',
        'views/mass_project_update_wizard_view.xml',
        'views/sh_project_stage_template.xml',
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 15,
    "currency": "EUR"
}
