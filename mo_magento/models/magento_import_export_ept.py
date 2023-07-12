from odoo import models, fields, api
from .api_request import req
import logging


class MagentoImportExportEpt(models.TransientModel):
    _inherit = 'magento.import.export.ept'

    def import_sale_order_operation(self, instances):
        queue_ids = list()
        queue = self.env['magento.order.data.queue.ept']
        kwargs = {'from_date': self.start_date, 'to_date': self.end_date}
        for instance in instances:
            if self.operations == 'import_ship_sale_order':
                kwargs.update({'status': ['complete', 'delivered']})
            else:
                kwargs.update({'status': instance.import_magento_order_status_ids.mapped('status')})
            kwargs.update({'instance': instance})
            queue_ids += queue.create_order_queues(**kwargs)
        action = 'odoo_magento2_ept.view_magento_order_data_queue_ept_form'
        model = 'magento.order.data.queue.ept'
        return self.env['magento.instance'].get_queue_action(ids=queue_ids, name="Order Queues",
                                                             model=model,
                                                             action=action)