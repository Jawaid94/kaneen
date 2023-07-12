from odoo import models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def create(self, vals):
        if not vals.get('lot_name', False):
            vals.update({'lot_name': self.env['ir.sequence'].next_by_code('stock.lot')})
            return super(StockMoveLine, self).create(vals)
        else:
            return super(StockMoveLine, self).create(vals)

    @api.onchange('location_id')
    def show_lot(self):
        self.lot_name = self.env['ir.sequence'].next_by_code('stock.lot')
