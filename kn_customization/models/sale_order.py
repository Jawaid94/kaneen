from odoo import fields,models,api, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    cust_gender = fields.Selection([('male', 'Male'), ('female', 'Female'),('none','None'),
                             ], string="Customer Gender")
    remarks = fields.Text(string="Additional Remarks")

    def create_cust_complaint(self):
        for rec in self:
            return {
                'name': _("Customer Complaint"),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'helpdesk.ticket',
                'context': {'default_so_id': rec.id,
                            'default_partner_id': rec.partner_id.id,
                            },
                'target': 'new',

            }