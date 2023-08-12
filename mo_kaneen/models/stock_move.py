from odoo import models, fields, _
from odoo.tools import OrderedSet, groupby


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

    def _action_done(self):
        super()._action_done()

        pickings = self.mapped('picking_id')
        if not pickings:
            return

        # pickings._update_reserve_from_customer()

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
