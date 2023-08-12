# -*- coding: iso-8859-1 -*-
from odoo import models, fields, api, _
from .xml_rpc_request import connect
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class StokQuant(models.Model):
    _inherit = 'stock.quant'

    def import_quant_from_shatha(self, rpc_connection=None, active_ids=None):
        url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
        db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
        username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
        password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
        # write_date = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_write_date_quant')
        shatha_location_id = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_location_id')
        # shatha_remote_location_id = int(
        #     self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_remote_stock_location_id'))
        if not rpc_connection:
            uid, models = connect(url, db, username, password)
        else:
            uid, models = rpc_connection

        location_id = self.env['stock.location'].browse(int(shatha_location_id))

        if not active_ids:
            curr_prods = self.env['product.product'].search([('sku_shatha', 'not in', [False, 'None'])])
            curr_prods_quant = self.env['product.product'].search([('sku_shatha', 'not in', [False, 'None'])])
        else:
            curr_prods = active_ids
            curr_prods_quant = active_ids
        current_skus = curr_prods.filtered(lambda x: x.default_code).mapped('default_code')
        current_shatha_skus = curr_prods.filtered(lambda x: x.sku_shatha).mapped('sku_shatha')
        current_skus.extend(current_shatha_skus)

        skus_all = list(set(current_skus))
        current_barcodes = curr_prods.filtered(lambda x: x.barcode).mapped('barcode')

        domain = []
        if skus_all:
            domain.append(['default_code', 'in', skus_all])
        if current_barcodes:
            barcodes = curr_prods.mapped("barcode_ids")
            if barcodes:
                current_barcodes.extend(barcodes.mapped('name'))

            domain.insert(0, "|")
            domain.append(['barcode', 'in', current_barcodes])

        search_product = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                           [domain], {'fields': ['default_code', 'barcode', 'product_tmpl_id']})

        _logger.error("Shatha stocks find products count {}".format(len(search_product)))

        if not search_product:
            return

        _logger.error("Updating products stocks from Shatha")

        prod_ids = []
        dict_prod = {}
        dict_prod_bc = {}
        for prod in search_product:
            dict_prod.update({
                prod['id']: prod['default_code']
            })
            dict_prod_bc.update({
                prod['id']: prod['barcode']
            })
            prod_ids.append(prod['id'])

        # quants = models.execute_kw(db, uid, password, 'stock.quant', 'search_read',
        #                            [[['product_id', 'in', prod_ids], '|',
        #                              ['location_id', 'child_of', shatha_remote_location_id],
        #                              ['location_id', '=', shatha_remote_location_id]]],
        #                            {'fields': ['product_id', 'available_quantity']})
        locations = models.execute_kw(db, uid, password, 'stock.location', 'search_read',
                                      [[['usage', '=', 'internal']]], {'fields': ['id']})
        location_ids = [location['id'] for location in locations]
        for product_id in curr_prods_quant:
            shatha_product_id = [product_vals['id'] for product_vals in search_product if
                                 product_vals['default_code'] == product_id.sku_shatha][0]

            quants = models.execute_kw(db, uid, password, 'stock.quant', 'search_read',
                                       [[['product_id', '=', shatha_product_id], ['location_id', 'in', location_ids]]],
                                       {'fields': ['product_id', 'available_quantity', 'quantity']})

            if not quants:
                continue

            inventory_quantity = sum(quant['quantity'] for quant in quants)

            search_quant = self.search([('product_id', '=', product_id.id), ('location_id', '=', location_id.id)])

            if search_quant:
                if search_quant.quantity == inventory_quantity:
                    continue
                search_quant.write({
                    'inventory_quantity': inventory_quantity
                })

                search_quant.action_apply_inventory()

            else:
                self.create({
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'inventory_quantity': inventory_quantity
                }).action_apply_inventory()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Quants successfully updated"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }