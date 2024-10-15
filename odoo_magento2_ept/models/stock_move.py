# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Describes methods for stock move.
"""
from odoo import models
from .api_request import req
from odoo.tools import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class StockMove(models.Model):
    """
    Describes Magento order stock picking values
    """
    _inherit = 'stock.move'

    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        """ Create or update move lines.
        """
        self.ensure_one()

        if not lot_id:
            lot_id = self.env['stock.production.lot']
        if not package_id:
            package_id = self.env['stock.quant.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        # do full packaging reservation when it's needed
        if self.product_packaging_id and self.product_id.product_tmpl_id.categ_id.packaging_reserve_method == "full":
            available_quantity = self.product_packaging_id._check_qty(available_quantity, self.product_id.uom_id,
                                                                      "DOWN")

        taken_quantity = min(available_quantity, need)

        # `taken_quantity` is in the quants unit of measure. There's a possibility that the move's
        # unit of measure won't be respected if we blindly reserve this quantity, a common usecase
        # is if the move's unit of measure's rounding does not allow fractional reservation. We chose
        # to convert `taken_quantity` to the move's unit of measure with a down rounding method and
        # then get it back in the quants unit of measure with an half-up rounding_method. This
        # way, we'll never reserve more than allowed. We do not apply this logic if
        # `available_quantity` is brought by a chained move line. In this case, `_prepare_move_line_vals`
        # will take care of changing the UOM to the UOM of the product.
        if not strict and self.product_id.uom_id != self.product_uom:
            taken_quantity_move_uom = self.product_id.uom_id._compute_quantity(taken_quantity, self.product_uom,
                                                                               rounding_method='DOWN')
            taken_quantity = self.product_uom._compute_quantity(taken_quantity_move_uom, self.product_id.uom_id,
                                                                rounding_method='HALF-UP')

        quants = []
        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if self.product_id.tracking == 'serial':
            if float_compare(taken_quantity, int(taken_quantity), precision_digits=rounding) != 0:
                taken_quantity = 0

        self.env['base'].flush()
        try:
            with self.env.cr.savepoint():
                if not float_is_zero(taken_quantity, precision_rounding=self.product_id.uom_id.rounding):
                    quants = self.env['stock.quant']._update_reserved_quantity(
                        self.product_id, location_id, taken_quantity, lot_id=lot_id,
                        package_id=package_id, owner_id=owner_id, strict=strict
                    )
        except UserError:
            taken_quantity = 0

        # Find a candidate move line to update or create a new one.
        serial_move_line_vals = []
        for reserved_quant, quantity in quants:
            to_update = next(
                (line for line in self.move_line_ids if line._reservation_is_updatable(quantity, reserved_quant)),
                False)
            if to_update:
                uom_quantity = self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id,
                                                                        rounding_method='HALF-UP')
                uom_quantity = float_round(uom_quantity, precision_digits=rounding)
                uom_quantity_back_to_product_uom = to_update.product_uom_id._compute_quantity(uom_quantity,
                                                                                              self.product_id.uom_id,
                                                                                              rounding_method='HALF-UP')
            if to_update and float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                to_update.with_context(bypass_reservation_update=True).product_uom_qty += uom_quantity
            else:
                if self.product_id.tracking == 'serial':
                    # Move lines with serial tracked product_id cannot be to-update candidates. Delay the creation to speed up candidates search + create.
                    serial_move_line_vals.extend(
                        [self._prepare_move_line_vals(quantity=1, reserved_quant=reserved_quant) for i in
                         range(int(quantity))])
                else:
                    self.env['stock.move.line'].create(
                        self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))

            payload = {
                "skuData": [
                ]
            }
            if eval(self.product_id.sku_shatha) is None:

                picking = self.picking_id

                if picking.picking_type_code == 'outgoing' and picking.sale_id.magento_order_id is not False:
                    continue

                product = self.product_id

                magento_instance = self.env['magento.instance'].browse(1)

                quant_data = self.env['stock.quant'].read_group(
                    domain=[('product_id', '=', product.id), ('location_id.usage', '=', 'internal')],
                    fields=['available_quantity'], groupby=['product_id']
                )

                available_qty = quant_data[0]['available_quantity'] if quant_data else 0.0

                payload['skuData'].append(
                    {
                        "sku": product.default_code,
                        "qty": available_qty,
                        "is_in_stock": 1 if available_qty > 0 else 0,
                    }
                )

            payload['skuData'] = [ele for index, ele in enumerate(payload['skuData']) if
                                  ele not in payload['skuData'][index + 1:]]

            if payload['skuData']:

                req(magento_instance, '/V1/product/updatestock', 'PUT', payload, is_raise=True)

        self.env['stock.move.line'].create(serial_move_line_vals)
        return taken_quantity

    def _get_new_picking_values(self):
        """
        We need this method to set our custom fields in Stock Picking
        :return:
        """
        res = super(StockMove, self)._get_new_picking_values()
        sale_order = self.group_id.sale_id
        sale_line_id = sale_order.order_line
        if sale_order and sale_line_id and sale_order.magento_instance_id:
            res.update({
                'magento_instance_id': sale_order.magento_instance_id.id,
                'is_exported_to_magento': False,
                'is_magento_picking': True
            })
            if sale_order.magento_instance_id.is_multi_warehouse_in_magento:
                inv_loc = self.env['magento.inventory.locations'].search([
                    ('ship_from_location', '=', res.get('location_id')),
                    ('magento_instance_id', '=', sale_order.magento_instance_id.id)
                ])
                if inv_loc:
                    res.update({'magento_inventory_source': inv_loc.id})
        return res

    def _action_assign(self):
        """
        In Dropshipping case, While create picking
        set magento instance id and magento picking as True
        if the order is imported from the Magento Instance.
        :return:
        """
        res = super(StockMove, self)._action_assign()
        picking_ids = self.mapped('picking_id')
        for picking in picking_ids:
            if not picking.magento_instance_id and picking.sale_id and picking.sale_id.magento_instance_id:
                picking.write({
                    'magento_instance_id': picking.sale_id.magento_instance_id.id,
                    'is_exported_to_magento': False,
                    'is_magento_picking': True
                })
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _action_done(self):
        super(StockMoveLine, self)._action_done()
        payload = {
            "skuData": [
            ]
        }

        magento_instance = self.env['magento.instance'].browse(1)

        for ml in self:
            if eval(ml.product_id.sku_shatha) is None:

                picking = ml.picking_id

                if picking.picking_type_code == 'outgoing' and picking.sale_id.magento_order_id is not False:
                    continue

                product = ml.product_id

                quant_data = self.env['stock.quant'].read_group(
                    domain=[('product_id', '=', product.id), ('location_id.usage', '=', 'internal')],
                    fields=['available_quantity'], groupby=['product_id']
                )

                available_qty = quant_data[0]['available_quantity'] if quant_data else 0.0

                payload['skuData'].append(
                    {
                        "sku": product.default_code,
                        "qty": available_qty,
                        "is_in_stock": 1 if available_qty > 0 else 0,
                    }
                )

        payload['skuData'] = [ele for index, ele in enumerate(payload['skuData']) if
                              ele not in payload['skuData'][index + 1:]]

        if payload['skuData']:
            req(magento_instance, '/V1/product/updatestock', 'PUT', payload, is_raise=True)
