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
        write_date = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_write_date_quant')
        shatha_location_id = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_location_id')
        shatha_remote_location_id = int(
            self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_remote_stock_location_id'))
        if not rpc_connection:
            uid, models = connect(url, db, username, password)
        else:
            uid, models = rpc_connection

        location_id = self.env['stock.location'].browse(int(shatha_location_id))

        if not active_ids:
            curr_prods = self.env['product.product'].search([])
            curr_prods_quant = self.env['product.product'].search([])
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

        _logger.error("Shata stocks find products count {}".format(len(search_product)))

        if not search_product:
            return

        _logger.error("Updating products stocks from Shata")

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

        quants = models.execute_kw(db, uid, password, 'stock.quant', 'search_read',
                                   [[['product_id', 'in', prod_ids], '|',
                                     ['location_id', 'child_of', shatha_remote_location_id],
                                     ['location_id', '=', shatha_remote_location_id]]],
                                   {'fields': ['product_id', 'available_quantity']})
        for quant in quants:
            if float(quant.get('available_quantity')) < 0:
                continue
            # search_product = models.execute_kw(db, uid, password, 'product.product', 'search_read',
            #                                    [[['id', '=', quant.get('product_id')[0]]]],
            #                                    {'fields': ['default_code'], 'limit': 1})
            code = dict_prod[quant['product_id'][0]]
            bc = dict_prod_bc[quant['product_id'][0]]
            product_id = self.env['product.product'].search(
                [('sku_shatha', '=', code)])
            if not product_id:
                product_id = self.env['product.product'].search(
                    [('default_code', '=', code)])
                if not product_id:
                    product_id = self.env['product.product'].search(
                        [('barcode', '=', bc)])
                    if not product_id:
                        continue

            search_quant = self.search([('product_id', '=', product_id.id), ('location_id', '=', location_id.id)])
            if search_quant and search_quant.quantity != float(quant.get('available_quantity')):
                search_quant.write({
                    'inventory_quantity': float(quant.get('available_quantity'))
                })
                search_quant.action_apply_inventory()
            elif search_quant and search_quant.quantity == float(quant.get('available_quantity')):
                curr_prods_quant -= product_id
                continue
            else:
                self.create({
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'inventory_quantity': float(quant.get('available_quantity'))
                }).action_apply_inventory()
            curr_prods_quant -= product_id
        if curr_prods_quant:
            for prod in curr_prods_quant:
                search_quant = self.search([('product_id', '=', prod.id), ('location_id', '=', location_id.id)])
                if search_quant.reserved_quantity:
                    search_quant.write({'inventory_quantity': search_quant.reserved_quantity})
                else:
                    search_quant.write({'inventory_quantity': 0})
                search_quant.action_apply_inventory()

        if not active_ids:
            tmpls = curr_prods.mapped('product_tmpl_id')
            self.env['product.template'].with_context(active_ids=tmpls.ids).import_product_from_shatha(
                rpc_connection=(uid, models), from_quant=True)

            write_date = self.env['ir.config_parameter'].sudo().set_param('mo_kaneen.shatha_write_date_quant',
                                                                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Quants successfully updated"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
