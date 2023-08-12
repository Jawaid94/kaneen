# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Describes methods to store Order Data queue line
"""
import json
import pytz
from odoo import models, fields, _
from dateutil import parser

utc = pytz.utc


class MagentoOrderDataQueueLineEpt(models.Model):
    _inherit = "magento.order.data.queue.line.ept"

    def process_order_queue_line(self, line, log):
        item = json.loads(line.data)
        order_ref = item.get('increment_id')
        order = self.env['sale.order']
        instance = self.instance_id
        is_exists = order.search([('magento_instance_id', '=', instance.id),
                                  ('magento_order_reference', '=', order_ref)])
        if is_exists:
            if item.get('status') == 'processing':
                is_exists.magento_order_status = 'processing'
            if item.get('status') == 'complete':
                is_exists.write(
                    {'state': 'complete' if is_exists.payment_status == 'paid' else 'delivered'}
                )
                is_exists.magento_order_status = 'complete'
            return True
        create_at = item.get("created_at", False)
        # Need to compare the datetime object
        date_order = parser.parse(create_at).astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
        if str(instance.import_order_after_date) > date_order:
            message = _(f"""
            There is a configuration mismatch in the import of order #{order_ref}.\n
            The order receive date is {date_order}.\n
            Please check the date set in the configuration in Magento2 Connector -> Configuration 
            -> Setting -> Select Instance -> 'Import Order After Date'.
            """)
            log.write({'log_lines': [(0, 0, {
                'message': message, 'order_ref': line.magento_id,
                'magento_order_data_queue_line_id': line.id
            })]})
            return False
        is_processed = self.financial_status_config(item, instance, log, line)
        if is_processed:
            carrier = self.env['delivery.carrier']
            is_processed = carrier.find_delivery_carrier(item, instance, log, line)
            if is_processed:
                # add create product method
                item_ids = self.__prepare_product_dict(item.get('items'))
                m_product = self.env['magento.product.product']
                p_items = m_product.with_context(is_order=True).get_products(instance, item_ids, line)

                order_item = self.env['sale.order.line'].find_order_item(item, instance, log, line.id)
                if not order_item:
                    if p_items:
                        p_queue = self.env['sync.import.magento.product.queue.line']
                        self._update_product_type(p_items, item)
                        for p_item in p_items:
                            is_processed = p_queue.with_context(is_order=True).import_products(p_item, line)
                            if not is_processed:
                                break
                    else:
                        is_processed = False
                if is_processed:
                    is_processed = order.create_sale_order_ept(item, instance, log, line.id)
                    if is_processed:
                        line.write({'sale_order_id': item.get('sale_order_id').id})
        return is_processed
