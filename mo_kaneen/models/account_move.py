from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Move(models.Model):
    _inherit = 'account.move'

    return_picking_id = fields.Many2one('stock.picking', string="Return Picking")

    def _post(self, soft=True):
        res = super()._post(soft)
        todo = self.env['sale.order']
        for move in self:
            if move.state == 'posted' and move.is_invoice():
                for line in move.invoice_line_ids:
                    for sale_line in line.sale_line_ids:
                        todo |= sale_line.order_id

        for order in todo:
            if order.state not in ['shipped', 'ready_to_ship', 'damaged_item', 'item_returned']:
                order.write({
                    'state': 'processing'
                })
        return res

    def action_post(self):
        for move in self.filtered(lambda x: x.move_type == 'out_refund'):
            if not move.return_picking_id:
                continue

            if move.return_picking_id.state != 'done':
                raise ValidationError(
                    _("Return picking {} for refund {} is not done!").format(move.return_picking_id.name, move.name))

        super(Move, self).action_post()
        # template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        for invoice in self:
            if invoice.move_type != 'out_refund':
                email_template_obj = self.env.ref('mo_kaneen.mo_mail_template_invoice_confirm',
                                                  raise_if_not_found=False)
                msg_id = email_template_obj.send_mail(invoice.id)

                mail_mail_obj = self.env['mail.mail'].browse(msg_id)

                if msg_id:
                    mail_mail_obj.send()


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    taxable_amount = fields.Monetary(string="Taxable Amount", compute="_compute_amount_taxable", store='True', help="")

    @api.depends('quantity', 'price_unit')
    def _compute_amount_taxable(self):
        for r in self:
            r.taxable_amount = r.quantity * r.price_unit
