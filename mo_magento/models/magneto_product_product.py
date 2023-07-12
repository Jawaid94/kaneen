import logging
from odoo import fields, models, _


_logger = logging.getLogger('MagentoEPT')


class MagentoProductProduct(models.Model):
    """
    Describes fields and methods for Magento products
    """
    _inherit = 'magento.product.product'

    def _prepare_product_values(self, item):
        values = {
            'name': item.get('name'),
            'default_code': item.get('sku'),
            'type': 'product',
            'invoice_policy': 'order',
            'published_web_status': True
        }
        route_ids = self.env['stock.location.route'].search([]).filtered(
            lambda x: x.name == 'Buy' or x.name == 'Make To Order + Make To Stock')
        values.update({
            'route_ids': [(6, 0, route_ids.ids)],
        })

        description = self.prepare_description(item)
        if description:
            values.update(description)
        return values