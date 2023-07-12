from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    default_dest_loc_id = fields.Many2one('stock.location', string="Default Destination")