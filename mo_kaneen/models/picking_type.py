from odoo import models, fields, api, _


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    picking_type_for_putaway = fields.Many2one("stock.picking.type", string="Operation Type For Return Putaway")
    visible_putaway = fields.Boolean(compute="_compute_putaway")

    def _compute_putaway(self):
        for p_type in self:
            use = self.search([('return_picking_type_id', '=', p_type.id)])
            if not use:
                p_type.visible_putaway = False
            else:
                p_type.visible_putaway = True