from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    image_256 = fields.Binary(related='product_id.image_512')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    image_256 = fields.Binary(related='product_id.image_512', string='Product Image')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    image_256 = fields.Binary(related='product_id.image_512', string='Product Image')
    barcode = fields.Text(compute='_compute_barcode')
    location = fields.Text(compute='_compute_location')

    def _compute_barcode(self):
        for record in self:
            record.barcode = record.product_id.barcode
            if record.product_id.barcode_ids:
                record.barcode += ', '
                record.barcode += ', '.join(record.product_id.barcode_ids.mapped('name'))

    def _compute_location(self):
        for record in self:
            if record.product_id.sku_shatha:
                if eval(record.product_id.sku_shatha) is None:
                    quants = record.product_id.stock_quant_ids.filtered(lambda quant: quant.inventory_date)
                    record.location = ', '.join(val[-1] for val in quants.location_id.name_get())
                else:
                    record.location = False
            else:
                record.location = False
