import logging
from odoo import fields, models, _
from odoo.tools.misc import split_every


_logger = logging.getLogger('MagentoEPT')


class MagentoProductTemplate(models.Model):
    _inherit = 'magento.product.template'

    def _update_price_cron(self,  active_ids=False, spit_every=80, instance=False):
        if not active_ids:
            active_ids = self.env['magento.product.template'].search([('sync_product_with_magento', '=', True)]).ids

        if spit_every > 80:
            spit_every = 80
        active_ids_ar = split_every(spit_every, active_ids)

        for arr in active_ids_ar:
            wiz = self.env['magento.export.product.ept'].create({
                "update_price": True
            })

            wiz.with_context(active_ids=list(arr)).process_update_products_in_magento()