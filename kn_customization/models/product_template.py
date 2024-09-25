from odoo import fields,models,api


class inheritProductTemplate(models.Model):
    _inherit = 'product.template'


    state = fields.Selection(
        [('category', 'Category Team'), ('catalogue', 'Catalogue Team'), ('magento', 'Magento Team'), ('ready', 'Catalogue approval'), ('publish', 'Published')],
        string='Product Status', default='category', tracking=True)

    def confirm_category_team(self):
        for rec in self:
            rec.state = 'catalogue'

    def confirm_catalogue_team(self):
        for rec in self:
            rec.state = 'magento'

    def confirm_magento_team(self):
        for rec in self:
            rec.state = 'ready'

    def publish_catalogue_team(self):
        for rec in self:
            rec.state = 'publish'

