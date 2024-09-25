# -*- coding: iso-8859-1 -*-
import logging
from odoo import models, fields, api, _
from .xml_rpc_request import connect
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.osv.expression import OR

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sku_shatha = fields.Char(default='None')

    def import_product_from_shatha(self, rpc_connection=None, from_quant=False):
        url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
        db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
        username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
        password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
        write_date = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_write_date_product')
        if not rpc_connection:
            uid, models = connect(url, db, username, password)
        else:
            uid, models = rpc_connection

        if self._context.get('active_ids'):
            curr_prods = self.browse(self._context['active_ids'])
        else:
            curr_prods = self.env['product.template'].search([])

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

        if self._context.get('active_ids'):
            products = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                         [domain], {'fields': ['name', 'id', 'default_code', 'barcode', 'list_price']})
        else:
            domain.insert(0, ['write_date', '>', write_date])
            products = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                         [domain], {'fields': ['name', 'id', 'default_code', 'barcode', 'list_price']})

        _logger.error("Shata find products count {}".format(len(products)))

        if not products and self._context.get('active_ids'):
            raise ValidationError("Can not find given products in Shatha")
        elif not products:
            return

        _logger.error("Updating products from Shata")

        to_update_stock = self.env['product.product']
        for product in products:
            domain = []
            if product.get('default_code'):
                domain.append(('default_code', '=', product['default_code']))
                domain = OR([domain, [('sku_shatha', '=',  product['default_code'])]])
            if product.get('barcode'):
                domain = OR([domain, [('barcode', '=', product['barcode'])]])

            search_product = self.search(domain)
            if search_product:
                vendor = search_product.seller_ids.filtered(lambda x: x.name.name == 'Shatha AlKhaleej')
                if vendor:
                    vendor.write({
                        'price': float(product.get('list_price'))
                    })

                to_update_stock |= search_product.product_variant_ids[0]
            else:
                _logger.info("No product {}".format(domain))

        if to_update_stock and not from_quant:
            self.env['stock.quant'].import_quant_from_shatha((uid, models), to_update_stock)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Products successfully updated"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

        arr = [('sku_shatha', self.search([('sku_shatha', '!=', False)]).mapped('sku_shatha')),
               ('default_code', self.search([]).mapped('default_code'))]

        def update(instanse, codes):
            products = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                         [[['write_date', '>', write_date],
                                           ['default_code', 'in', codes]]],
                                         {'fields': ['name', 'id', 'default_code', 'list_price']})
            for product in products:
                search_product = self.search([(instanse, '=', product.get('default_code'))])
                if search_product:
                    vendor = search_product.seller_ids.filtered(lambda x: x.name.name == 'Shatha AlKhaleej')
                    if vendor:
                        vendor.write({
                            'price': float(product.get('list_price'))
                        })

        for item in arr:
            update(item[0], item[1])
        write_date = self.env['ir.config_parameter'].sudo().set_param('mo_kaneen.shatha_write_date_product',
                                                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Products successfully updated"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def _get_fields_stock_barcode(self):
        res = super()._get_fields_stock_barcode()
        res.append('barcode_ids')
        return res
