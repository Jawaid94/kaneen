from odoo import models, fields, api
from .api_request import req
import logging
import requests

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    export_shipped = fields.Boolean()

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        request = req(self.magento_instance_id, '/all/V1/orders/' + self.magento_order_id, 'GET',
                      {"entity_id": self.magento_order_id}, is_raise=True, return_text=True)
        if request.get('status') == 'canceled':
            return
        data = {
            "entity": {
                "entity_id": self.magento_order_id,
                "status": 'canceled'
            }
        }
        request = req(self.magento_instance_id, '/all/V1/orders', 'POST', data, is_raise=True)
        if 'message' in request:
            _logger.info("Can not send status to magento {} {}".format(self.name, request['message']))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': request['message'],
                    'sticky': True,
                }
            }
        return res

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'shipped' and self.export_shipped:
            return

        if self.state == 'ready_to_ship' or self.state == 'shipped':
            request = req(self.magento_instance_id, '/all/V1/orders/' + self.magento_order_id, 'GET',
                          {"entity_id": self.magento_order_id}, is_raise=True, return_text=True)
            if request.get('status') == 'complete' or request.get('status') == 'cancel':
                return
            data = {
                "entity": {
                    "entity_id": self.magento_order_id,
                    "status": self.state
                }
            }
            request = req(self.magento_instance_id, '/all/V1/orders', 'POST', data, is_raise=True)
            if 'message' in request:
                _logger.info("Can not send status to magento {} {}".format(self.name, request['message']))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'message': request['message'],
                        'sticky': True,
                    }
                }

            if self.state == 'shipped':
                self.sudo().write({
                    'export_shipped': True
                })

    def onchange_state_cron(self):
        records = self.search([('state', 'in', ['ready_to_ship', 'shipped']), ('magento_order_id', '!=', False)])
        for record in records:
            record.onchange_state()

    def create_sale_order_ept(self, item, instance, log, line_id):
        is_processed = self._find_price_list(item, log, line_id)
        order_line = self.env['sale.order.line']
        if is_processed:
            customers = self.__update_partner_dict(item, instance)
            magento_storeview_code = item.get('store_view').magento_storeview_code
            if magento_storeview_code == 'ar':
                customers_lang = 'ar_001'
            else:
                customers_lang = 'en_US'
            data = self.env['magento.res.partner.ept'].create_magento_customer(customers, True, lang=customers_lang)
            item.update(data)
            is_processed = self.__find_order_warehouse(item, log, line_id)
            if is_processed:
                is_processed = order_line.find_order_item(item, instance, log, line_id)
                if is_processed:
                    is_processed = self.__find_order_tax(item, instance, log, line_id)
                    if is_processed:
                        vals = self._prepare_order_dict(item, instance)
                        magento_order = self.create(vals)
                        item.update({'sale_order_id': magento_order})
                        order_line.create_order_line(item, instance, log, line_id)
                        self.__create_discount_order_line(item)
                        self.__create_shipping_order_line(item)

                        # self.__process_order_workflow(item, log)
        return is_processed


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def create_order_line(self, item, instance, log, line_id):
        order_lines = item.get('items')
        rounding = bool(instance.magento_tax_rounding_method == 'round_per_line')
        for line in order_lines:
            if line.get('product_type') in ['configurable', 'bundle']:
                continue
            product = line.get('line_product')
            price = self.__find_order_item_price(item, line)
            customer_option = self.__get_custom_option(item, line)
            line_vals = self.with_context(custom_options=customer_option).prepare_order_line_vals(
                item, line, product, price)
            order_line = self.create(line_vals)
            order_line.with_context(round=rounding)._compute_amount()
            self.__create_line_desc_note(customer_option, item.get('sale_order_id'))
        if item.get('sale_order_id').magento_payment_method_id.payment_method_code == 'cashondelivery':
            product = self.env['product.product'].search(
                [('name', '=', 'Payment Fee'), ('default_code', '=', 'MAGENTO_PAY')])
            if product:
                total = item.get('base_total_due') if item.get('base_total_due') != 0 else item.get('base_total_paid')
                discount = item.get('base_discount_amount', 0) * -1
                self.create({
                    'order_id': item.get('sale_order_id').id,
                    'product_id': product.id,
                    'company_id': item.get('sale_order_id').company_id.id,
                    'price_unit': total - item.get('base_subtotal_incl_tax', 0) - item.get(
                        'base_shipping_incl_tax', 0) + discount,
                })
        return True
