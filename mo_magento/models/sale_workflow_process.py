from odoo import models, fields, api
from odoo.addons.stock.models.stock_rule import ProcurementException


class SaleWorkflowProcess(models.Model):
    _inherit = "sale.workflow.process.ept"

    @api.model
    def auto_workflow_process_ept(self, auto_workflow_process_id=False, order_ids=[]):
        """
        This method will find draft sale orders which are not having invoices yet, confirmed it and done the payment
        according to the auto invoice workflow configured in sale order.
        :param auto_workflow_process_id: auto workflow process id
        :param order_ids: ids of sale orders
        Migration done by Haresh Mori on September 2021
        """
        sale_order_obj = self.env['sale.order']
        workflow_process_obj = self.env['sale.workflow.process.ept']
        if not auto_workflow_process_id:
            work_flow_process_records = workflow_process_obj.search([])
        else:
            work_flow_process_records = workflow_process_obj.browse(auto_workflow_process_id)

        if not order_ids:
            # orders = sale_order_obj.search([('auto_workflow_process_id', 'in', work_flow_process_records.ids),
            #                                 ('state', 'not in', ('done', 'cancel', 'sale')),
            #                                 ('invoice_status', '!=', 'invoiced')])

            orders = sale_order_obj.search([('auto_workflow_process_id', 'in', work_flow_process_records.ids),
                                            ('state', 'in', ['draft']),
                                            ('invoice_status', '!=', 'invoiced')])
        else:
            orders = sale_order_obj.search([('auto_workflow_process_id', 'in', work_flow_process_records.ids),
                                            ('id', 'in', order_ids)])

        for order in orders:
            try:
                order.process_orders_and_invoices_ept()
            except ProcurementException:
                continue
            except Exception:
                continue

        return True