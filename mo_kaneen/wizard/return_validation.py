from ..models.sale_order import quality_items
from odoo import models, fields, api


class ReturnValidation(models.TransientModel):
    _name = 'return.validation'
    _description = "Return Validation"

    picking_id = fields.Many2one('stock.picking')
    line_ids = fields.One2many("return.validation.line", "wiz_id")

    @api.model
    def default_get(self, fields):
        defaults = super(ReturnValidation, self).default_get(fields)
        res_ids = self._context.get('active_ids')

        picking = self.env['stock.picking'].browse(res_ids)

        lines = []
        for line in picking.move_ids_without_package:
            qty = line.quantity_done
            if qty == 0:
                continue
            comments = line.return_comments

            comments_arr = []
            if comments:
                comments_arr = comments.split(";")
            for item in range(0, int(qty)):
                val = {
                    'product_id': line.product_id.id,
                    'move_id': line.id,
                    'sale_line_id': line.sale_line_id.id,
                    'qty': 1,
                    'original_qty': qty
                }
                if comments:
                    try:
                        val['return_comment'] = comments
                    except IndexError:
                        pass
                lines.append((0, 0, val))

        defaults.update({
            'picking_id': picking.id,
            'line_ids': lines
        })

        return defaults

    def validate(self):
        damaged = []
        for line in self.line_ids:
            val = {
                'sale_line_id': line.sale_line_id.id,
                'qty': line.qty,
                'product_quality': line.product_quality,
                'return_comment': line.return_comment,
                'move_id': line.move_id.id
            }
            if line.product_quality_comment_id:
                val['product_quality_comment_id'] = [(4, comm.id) for comm in line.product_quality_comment_id]

            damaged.append(val)

        if damaged:
            self.env['mo.damaged.item'].create(damaged)

        res = self.picking_id.with_context(skip_return_validation=True).button_validate()
        if res is not True:
            return res


class ReturnValidationLine(models.TransientModel):
    _name = 'return.validation.line'
    _description = "Return Validation Line"

    wiz_id = fields.Many2one('return.validation', ondelete='cascade')
    picking_id = fields.Many2one("stock.picking")
    sale_line_id = fields.Many2one('sale.order.line')
    move_id = fields.Many2one('stock.move')

    product_quality = fields.Selection(selection=quality_items, string="Product quality", default="original")
    product_quality_comment_id = fields.Many2many('mo.product.quality.comment', string="Product quality comment")

    return_comment = fields.Char(string="Return comment")

    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float("Quantity")
    original_qty = fields.Float("original Quantity")
