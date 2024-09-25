from odoo import fields,models,api, _


class HelpDeskInherit(models.Model):
    _inherit = 'helpdesk.ticket'

    so_id = fields.Many2one('sale.order', string="Sale Order")
    employee_id = fields.Many2one('hr.employee', string="Responsible")
    cust_gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('none', 'None'),
                                    ], string="Customer Gender")
    medium_id = fields.Many2one('utm.medium', 'Source')
