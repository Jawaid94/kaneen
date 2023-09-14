# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_operation_type = fields.Selection([('cancel', 'Cancel Only'), ('cancel_draft', 'Cancel and Reset to Draft'), ('cancel_delete', 'Cancel and Delete')],
                                              default='cancel', string="Invoice Opration Type")

    payment_operation_type = fields.Selection([('cancel', 'Cancel Only'), ('cancel_draft', 'Cancel and Reset to Draft'), ('cancel_delete', 'Cancel and Delete')],
                                              default='cancel', string="Payment Opration Type")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_operation_type = fields.Selection(default=lambda self: self.env.user.company_id.invoice_operation_type, related="company_id.invoice_operation_type", readonly=False)

    payment_operation_type = fields.Selection(default=lambda self: self.env.user.company_id.payment_operation_type, string="Payment Opration Type", related="company_id.payment_operation_type", readonly=False)
