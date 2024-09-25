from odoo import fields,models,api
from odoo.exceptions import AccessDenied, UserError, ValidationError


class inheritProductTemplate(models.Model):
    _inherit = 'stock.picking'

    inv_attachment = fields.Many2many('ir.attachment', string="Invoice Attachment")

    @api.constrains('inv_attachment')
    def _check_file(self):
        if len(self.inv_attachment) > 1:
            raise ValidationError("Kindly Attach Only One Attachment")
        if self.inv_attachment and not self.inv_attachment.name.lower().endswith('.pdf'):
            raise ValidationError("Cannot upload file different from .pdf file")