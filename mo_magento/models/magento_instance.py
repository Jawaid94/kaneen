from odoo import models, fields, api
from datetime import datetime


class MagentoInstance(models.Model):
    _inherit = 'magento.instance'

    @api.model
    def _default_payment_fee_product(self):
        product = self.env['product.product'].search(
            [('name', '=', 'Payment Fee'), ('default_code', '=', 'MAGENTO_PAY')])
        if not product:
            product = self.env['product.product'].create({
                'name': 'Payment Fee',
                'default_code': 'MAGENTO_PAY',
                'detailed_type': 'service',
                'taxes_id': self.env.company.account_sale_tax_id
            })
        return product.id

    payment_fee_product_id = fields.Many2one('product.product', default=_default_payment_fee_product)

    @api.model
    def _scheduler_import_product(self, args=None):
        """
        This method is used to import product from Magento via cron job.
        :param args: arguments to import products
        :return:
        """
        if not args:
            return True
        product_queue = self.env['sync.import.magento.product.queue']
        instance = self.env['magento.instance']
        instance_id = args.get('magento_instance_id')
        is_update = args.get('update_existing_product', False)
        if instance_id:
            instance = instance.browse(instance_id)
            from_date = ''
            if instance.last_product_import_date:
                from_date = instance.last_product_import_date
            to_date = datetime.now()
            p_types = ['simple']
            for p_type in p_types:
                product_queue.create_product_queues(instance, from_date, to_date, p_type, is_update)
            instance.write({
                'last_product_import_date': datetime.now()
            })
        return True
