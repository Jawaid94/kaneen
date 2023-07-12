# -*- coding: utf-8 -*-
"""
Describes methods to store sync/ Import product queue line
"""
import json
from datetime import datetime
from odoo import models, fields, _


class MagentoProductQueueLine(models.Model):
    """
    Describes sync/ Import product Queue Line
    """
    _inherit = "sync.import.magento.product.queue.line"

    def import_products(self, item, line):
        instance = line.instance_id
        m_product = self.env['magento.product.product']
        attribute = item.get('extension_attributes', {})
        if item.get('type_id') == 'simple':
            if 'simple_parent_id' in list(attribute.keys()):
                m_product = m_product.search([('magento_product_id', '=', item.get('id'))], limit=1)
                if not m_product or 'is_order' in list(self.env.context.keys()) or line.do_not_update_existing_product:
                    # This case only runs when we get the simple product which are used as an
                    # Child product of any configurable product in Magento.

                    return m_product.search_product_in_layer(line, item)

                    items = m_product.get_products(instance, [attribute.get('simple_parent_id')], line)
                    for item in items:
                        return m_product.import_configurable_product(line, item)
            else:
                # This case identifies that we get only simple product which are not set as an
                # Child product of any configurable product.
                return m_product.search_product_in_layer(line, item)
        elif item.get('type_id') == 'configurable':
            return m_product.import_configurable_product(line, item)
        elif item.get('type_id') in ['virtual', 'downloadable']:
            return m_product.search_service_product(item, line)
        else:
            # We are not allowing to import other types of products. Add log for that.
            return self.__search_product(line, item)
        return True