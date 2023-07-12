from odoo import models, fields, api


class MagentoImportExportEpt(models.Model):
    _inherit = 'magento.financial.status.ept'

    @staticmethod
    def __get_status_code(order_status, is_invoice, is_shipment):
        """
        Get Financial Status Dictionary.
        :param order_status: Order status received from Magento.
        :param is_invoice: Order is invoiced.
        :param is_shipment: Order is Shipped.
        :return: Financial Status dictionary
        """
        status_code = ''
        if order_status == "pending":
            status_code = 'not_paid'
        elif order_status == "processing" and is_invoice and not is_shipment:
            status_code = 'processing_paid'
        elif order_status == "processing" and is_shipment and not is_invoice:
            status_code = 'processing_unpaid'
        elif order_status == "complete":
            status_code = 'paid'
        return status_code

    @staticmethod
    def __get_status_name(order_status, is_invoice, is_shipment):
        """
        Get Financial Status Dictionary.
        :param order_status: Order status received from Magento.
        :param is_invoice: Order is invoiced.
        :param is_shipment: Order is Shipped.
        :return: Financial Status dictionary
        """
        status_name = ''
        if order_status == "pending":
            status_name = 'Pending Orders'
        elif order_status == "processing" and is_invoice and not is_shipment:
            status_name = 'Processing orders with Invoice'
        elif order_status == "processing" and is_shipment and not is_invoice:
            status_name = 'Processing orders with Shipping'
        elif order_status == "complete":
            status_name = 'Completed Orders'
        return status_name

    def search_financial_status(self, order_response, magento_instance, payment_option):
        order_status_ojb = self.env['magento.order.status.ept']
        mapped_order_status = order_status_ojb.search([('magento_instance_id', '=', magento_instance.id),
                                                       ('m_order_status_code', '=', order_response.get('status'))])
        if order_response.get('state') == 'complete':
            mapped_order_status = order_status_ojb.search([('magento_instance_id', '=', magento_instance.id),
                                                           ('m_order_status_code', '=', order_response.get('state'))])

        is_invoice = order_response.get('extension_attributes').get('is_invoice')
        is_shipment = order_response.get('extension_attributes').get('is_shipment')
        status_name = self.__get_status_name(mapped_order_status.main_status, is_invoice, is_shipment)
        status_code = self.__get_status_code(mapped_order_status.main_status, is_invoice, is_shipment)
        workflow_config = self.env['magento.financial.status.ept'].search(
            [('magento_instance_id', '=', magento_instance.id),
             ('payment_method_id', '=', payment_option.id),
             ('financial_status', '=', status_code)])
        return {'workflow': workflow_config, 'status_name': status_name}
