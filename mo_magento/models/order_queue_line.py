# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
"""
Describes methods to store Order Data queue line
"""
import json
import pytz
from odoo import models, _
from odoo.fields import Date
from dateutil import parser
from odoo.tests import Form

utc = pytz.utc


class MagentoOrderDataQueueLineEpt(models.Model):
    _inherit = "magento.order.data.queue.line.ept"

    def _generate_return_order(self, picking):
        return_wizard = self.env['stock.return.picking'].with_context(active_id=picking.id,
                                                                      active_ids=picking.ids).create(
            {
                'location_id': picking.location_id.id, 'picking_id': picking.id,
            })
        return_wizard._onchange_picking_id()
        action = return_wizard.create_returns()
        return_picking = self.env["stock.picking"].browse(action["res_id"])
        wiz_act = return_picking.button_validate()
        wiz = Form(self.env[wiz_act['res_model']].with_context(wiz_act['context'])).save()
        wiz.process()

    def process_order_queue_line(self, line, log):
        item = json.loads(line.data)
        order_ref = item.get('increment_id')
        order = self.env['sale.order']
        instance = self.instance_id
        is_exists = order.search([('magento_instance_id', '=', instance.id),
                                  ('magento_order_reference', '=', order_ref)])
        if is_exists:
            if item.get('status') == 'processing':

                if is_exists.state == 'cancel':
                    is_exists.action_draft()

                if is_exists.state == 'draft':
                    is_exists.validate_order_ept()

                is_exists._create_order_invoice(item)

            if item.get('status') == 'complete':
                is_exists._create_order_invoice(item)

            if item.get('status') == 'closed':

                incoming_picking = is_exists.picking_ids.filtered(
                    lambda pick: pick.picking_type_code == 'incoming' and pick.state != 'cancel')

                outgoing_picking = is_exists.picking_ids.filtered(
                    lambda picking: picking.picking_type_code == 'outgoing' and picking.state != 'cancel')

                if outgoing_picking:
                    self._generate_return_order(outgoing_picking)

                if incoming_picking:
                    self._generate_return_order(incoming_picking)

                # Refund the invoice
                wiz_context = {
                    'active_model': 'account.move',
                    'active_ids': is_exists.invoice_ids.ids,
                    'default_journal_id': is_exists.invoice_ids.journal_id.id
                }

                comment_vals = list()
                if item['status_histories']:
                    comment_vals = [d for d in item['status_histories'] if d['status'] == 'closed']
                    comment_vals = sorted(comment_vals, key=lambda comment_val: comment_val['created_at'])

                refund_invoice_wiz = self.env['account.move.reversal'].with_context(wiz_context).create({
                    'reason': comment_vals[0]['comment'],
                    'refund_method': 'refund',
                    'date': Date.context_today(self.env.user),
                })
                refund_invoice = self.env['account.move'].browse(refund_invoice_wiz.reverse_moves()['res_id'])
                refund_invoice.action_post()

                action_data = refund_invoice.action_register_payment()
                wizard = Form(self.env['account.payment.register'].with_context(action_data['context'])).save()
                wizard.with_context(dont_redirect_to_payments=True).action_create_payments()

                is_exists.state = is_exists.magento_order_status = item.get('status')

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
