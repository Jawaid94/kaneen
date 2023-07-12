# -*- coding: iso-8859-1 -*-
from odoo import models, fields, api
from .api_request import req
from odoo.addons.odoo_magento2_ept.python_library.php import Php


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    available_in_magento = fields.Boolean()
    instance_ids = fields.Many2many('magento.instance')
    published_web_status = fields.Boolean("Published On Web Status")
    tranlate_field = fields.Char()

    def export_to_mangento(self):
        if not self.available_in_magento or not self.instance_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': ("Check fields 'Available in Magento' and 'Instance'"),
                    'sticky': True,
                }
            }
        for instance in self.instance_ids:
            pricelist = instance.pricelist_id
            item_pricelist = self.env['product.pricelist.item'].search([('product_tmpl_id', '=', self.id), ('pricelist_id', '=', pricelist.id)])

            product = self.env['magento.product.template'].search([('magento_sku', '=', self.default_code)])
            if not product:
                product = self.env['magento.product.product'].search([('magento_sku', '=', self.default_code)])

            if product:
                continue

            data = {
                "product": {
                    "sku": self.default_code,
                    "name": self.name,
                    # "price": item_pricelist.fixed_price if item_pricelist else self.list_price,
                    "price": self.list_price,
                    "attribute_set_id": "4",
                    "status": "0",
                    "weight": str(self.weight),
                    "extension_attributes": {
                        "stock_item": {
                            "qty": str(self.qty_available),
                            "is_in_stock": True if self.qty_available > 0 else False
                        }
                    },
                    "custom_attributes": [
                        {
                            "attribute_code": "short_description",
                            "value": self.description_sale
                        }]
                }
            }
            request = req(instance, '/en/V1/products', 'POST', data, is_raise=True)
            if self.tranlate_field:
                data['product']['name'] = self.tranlate_field
                request = req(instance, '/ar/V1/products', 'POST', data, is_raise=True)
                del data['product']['status']
                if request == 'error':
                    data['product']['name'] = self.tranlate_field + '1F'
                    request = req(instance, '/ar/V1/products', 'POST', data, is_raise=True)
                    data['product']['name'] = self.tranlate_field
                    request = req(instance, '/ar/V1/products', 'POST', data, is_raise=True)
                    if request == 'error':
                        return 'error'
            if 'message' in request:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': request['message'],
                        'sticky': True,
                    }
                }
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': 'Product successfully exported',
                    'sticky': False,
                }
            }

    def available_in_magento_func(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'available.magneto',
            'target': 'new',
            'context': {'active_ids': self.ids},
        }

    def disable_in_magento(self):
        for record in self:
            record.available_in_magento = False

    def export_to_mangento_cron(self):
        arr = []
        if not self:
            self = self.search([('available_in_magento', '=', True)])
        for record in self:
            if record.available_in_magento:
                t = record.export_to_mangento()
                if t == 'error':
                    arr.append(record.id)
