from odoo import models, fields, api


class AvailableMagneto(models.TransientModel):
    _name = 'available.magneto'

    instance_ids = fields.Many2many('magento.instance')

    def set_available(self):
        product = self.env['product.template'].browse(self._context['active_ids'])
        for item in product:
            item.write({
                'available_in_magento': True,
                'instance_ids': [(6, 0, self.instance_ids.ids)]
            })
