from odoo import models, fields, api
from odoo.tools import groupby

class StockMove(models.Model):
    _inherit = 'stock.move'

    has_damaged_item = fields.Boolean(compute="_compute_damage")
    damaged_items = fields.One2many('mo.damaged.item', 'move_id')

    return_comments = fields.Char(string="Return Comments")

    def _compute_damage(self):
        for move in self:
            if move.damaged_items.filtered(lambda x: x.product_quality in ['semi-damaged', 'damaged']):
                move.has_damaged_item = True
            else:
                move.has_damaged_item = False

    def _push_apply(self):
        if not self._context.get("ignore_push_apply"):
            return super()._push_apply()
        else:
            new_moves = []
            return self.env['stock.move'].concat(*new_moves)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.depends('product_id', 'picking_type_use_create_lots', 'lot_id.expiration_date')
    def _compute_expiration_date(self):
        for move_line in self:
            if move_line.lot_id.use_expiration_date:
                if not move_line.expiration_date:
                    move_line.expiration_date = move_line.lot_id.expiration_date
            else:
                move_line.expiration_date = False

    def _apply_putaway_strategy(self):
        super()._apply_putaway_strategy()

        if self._context.get('avoid_putaway_rules'):
            return
        self = self.with_context(do_not_unreserve=True)
        for package, smls in groupby(self, lambda sml: sml.result_package_id):
            smls = self.env['stock.move.line'].concat(*smls)
            for sml in smls:
                if sml.picking_id.group_id:
                    purchase = self.env['purchase.order'].search([('name', '=', sml.picking_id.group_id.name)])
                    if not purchase or sml.picking_type_id.code != 'internal' or sml.picking_type_id.sequence_code != 'INT':
                        continue

                    sml.location_dest_id = purchase.partner_id.default_dest_loc_id.id or sml.location_dest_id.id


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom, company_id,
                                                                 values, line)
        if eval(product_id.sku_shatha):
            from . import purchase_order
            shatha_standard_price = purchase_order.get_standard_price(self, product_id.sku_shatha)
            res['price_unit'] = shatha_standard_price + 5
        return res


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    use_expiration_date = fields.Boolean(related=False)

    def _get_dates(self, product_id=None):
        return {}
