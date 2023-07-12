from odoo import models, fields, api, _
from .sale_order import quality_items


class DamagedItem(models.Model):
    _name = 'mo.damaged.item'
    _description = "Returned Item"

    move_id = fields.Many2one('stock.move')
    sale_line_id = fields.Many2one('sale.order.line')
    sale_id = fields.Many2one(related="sale_line_id.order_id", store=True)
    product_id = fields.Many2one(related="sale_line_id.product_id", store=True)

    product_quality = fields.Selection(selection=quality_items, string="Product quality")
    product_quality_comment_id = fields.Many2many('mo.product.quality.comment', string="Product quality comment")

    return_comment = fields.Char(string="Return comment")

    qty = fields.Float("Quantity")
