# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShProjectProject(models.Model):
    _inherit = "project.project"

    sh_stage_template_id = fields.Many2one(
        'sh.project.stage.template', string="Stage Template")
    sh_stage_ids = fields.Many2many(
        "project.task.type",
        "project_task_type_rel",
        "project_id", "type_id", string="Stages")

    def action_mass_project_update(self):
        return {
            'name':
                'Mass Update',
            'res_model':
                'sh.project.project.mass.update.wizard',
            'view_mode':
                'form',
            'context': {
                'default_project_project_ids':
                    [(6, 0, self.env.context.get('active_ids'))]
            },
            'view_id':
                self.env.ref(
                    'sh_project_stages.sh_project_project_update_wizard_form_view').
                id,
            'target':
                'new',
            'type':
                'ir.actions.act_window'
        }

    @api.onchange('sh_stage_template_id')
    def _onchange_stage(self):
        self.sh_stage_ids = [(6, 0, self.sh_stage_template_id.stage_ids.ids)]
