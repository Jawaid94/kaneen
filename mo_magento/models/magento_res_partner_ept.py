# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
from odoo import models, fields


class MagentoResPartnerEpt(models.Model):
    _inherit = "magento.res.partner.ept"

    def create_magento_customer(self, line, is_order=False, lang='en_US'):
        if is_order:
            data = line
            instance = line.get('instance_id')
        else:
            data = json.loads(line.data)
            instance = line.instance_id
        customer = False
        if data.get('id'):
            customer = self.__search_customer(id=data.get('id'), instance_id=instance.id)
        if not customer:
            partner = self._create_odoo_partner(data, instance)
            values = self._prepare_magento_customer_values(partner_id=partner.id, instance=instance,
                                                           data=data, customer_id=data.get('id'))
            customer = self.create(values)
        data.update({'parent_id': customer.partner_id.id})
        customer.partner_id.write({'lang': lang})
        self._create_customer_addresses(data, instance)
        return data
