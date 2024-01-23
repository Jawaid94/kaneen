# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Describes methods for stock move.
"""
from odoo import models
from .api_request import req


class StockMove(models.Model):
    """
    Describes Magento order stock picking values
    """
    _inherit = 'stock.move'

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
        for ml in self:
            if ml.picking_code == 'incoming' and eval(ml.product_id.sku_shatha) is None:
                available_qty = self.env['stock.quant']._get_available_quantity(ml.product_id, ml.location_dest_id,
                                                                                ml.lot_id, strict=True)
                payload['skuData'].append(
                    {
                        "sku": ml.product_id.default_code,
                        "qty": available_qty,
                        "is_in_stock": 1,
                    })
        payload['skuData'] = [ele for index, ele in enumerate(payload['skuData']) if
                              ele not in payload['skuData'][index + 1:]]
        if payload['skuData']:
            req(self.env['magento.instance'].browse(1), '/V1/product/updatestock', 'PUT', payload, is_raise=True)
