from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    customer_service_email = fields.Char()
