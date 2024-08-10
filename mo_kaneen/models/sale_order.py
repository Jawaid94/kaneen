from odoo import models, fields, api
from odoo.tools import float_is_zero, float_compare

quality_items = [("original", 'Original'), ('semi-damaged', 'Semi-Damaged'), ('damaged', 'Damaged')]


class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state in ('draft', 'cancel'):
                line.invoice_status = 'no'
            elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
                line.invoice_status = 'invoiced'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        for line in self:
            if line.order_id.state in ['sale', 'done', 'ready_to_ship', 'shipped']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0


class Sale(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            if any(sale_line.is_backorder_product for sale_line in order.order_line):

                email_template_obj = self.env.ref('mo_kaneen.mail_template_backorder')

                msg_id = email_template_obj.send_mail(order.id)

                mail_mail_obj = self.env['mail.mail'].browse(msg_id)

                if msg_id:
                    mail_mail_obj.send()

        return super(Sale, self).action_confirm()

    state = fields.Selection([
        ('draft', 'New'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Pending'),
        ('processing', 'Processing'),
        ('ready_to_ship', 'Ready To Ship'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('complete', 'Complete'),
        ('waiting_for_ret', 'Waiting For Return'),
        ('item_returned', 'Item Returned'),
        ('damaged_item', 'Damaged Item'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('closed', 'Closed'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    damage_count = fields.Integer(string='Damaged Items', compute='_compute_damaged_ids')

    def _compute_damaged_ids(self):
        for order in self:
            damaged_items = self.env['mo.damaged.item'].search([('sale_id', '=', order.id)])
            order.damage_count = len(damaged_items)

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        unconfirmed_orders = self.filtered(lambda so: so.state in ['draft', 'cancel'])
        unconfirmed_orders.invoice_status = 'no'

        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                ('order_id', 'in', confirmed_orders.ids),
                ('is_downpayment', '=', False),
                ('display_type', '=', False),
            ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state in ('draft', 'cancel'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(
                    invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.depends("invoice_ids.payment_state")
    def _sale_order_payment_status(self):
        for sale in self:
            invoices = sale.mapped('invoice_ids')
            if not invoices:
                sale.payment_status = 'not_paid'
            else:
                if all(invoice.payment_state == 'paid' or invoice.payment_state == 'in_payment' for invoice in
                       invoices) and all(invoice.type_name != 'Credit Note' for invoice in invoices):
                    # all paid
                    sale.payment_status = 'paid'
                    if sale.state == 'delivered':
                        sale.state = 'complete'
                elif any(invoice.type_name == 'Credit Note' for invoice in invoices) and any(
                        invoice.payment_state == 'not_paid' for invoice in invoices) and len(invoices) > 1:
                    sale.payment_status = 'waiting_for_refund'
                elif any(invoice.type_name == 'Credit Note' for invoice in invoices) and any(
                        invoice.payment_state == 'paid' or invoice.payment_state == 'in_payment' for invoice in
                        invoices) and len(invoices) > 1:
                    sale.payment_status = 'paid_and_refund'
                elif any(invoice.payment_state != 'paid' or 'in_payment' for invoice in invoices) and any(
                        invoice.payment_state == 'paid' or 'in_payment' for invoice in invoices) and len(invoices) > 1:
                    # any not paid and some paid
                    sale.payment_status = 'partial'
                elif all(invoice.payment_state == 'partial' for invoice in invoices):
                    # all partial
                    sale.payment_status = 'partial'
                elif all(invoice.payment_state == 'not_paid' for invoice in invoices):
                    # all not paid
                    sale.payment_status = 'not_paid'
                else:
                    sale.payment_status = 'not_paid'

    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('waiting_for_refund', 'Waiting for Refund'),
        ('paid_and_refund', 'Paid and Refund'),
    ], string='Payment State', compute="_sale_order_payment_status", store=True, readonly=True)

    def open_return(self):
        view = self.env.ref('stock.view_stock_return_picking_form')
        picking = self.picking_ids.filtered(lambda x: x.picking_type_code == 'outgoing' and x.state == 'done')
        if not picking:
            return
        return {
            'name': 'Return',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.return.picking',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': {
                'default_picking_id': picking[0].id,
                'sale_order_id': self.id,
            },
        }

    def open_damaged(self):
        action = self.env["ir.actions.actions"]._for_xml_id("mo_kaneen.mo_damaged_item_action")

        action['domain'] = [('sale_id', 'in', self.ids)]
        return action

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids.filtered(lambda x: not x.show_in_purchase))

    def action_view_delivery(self):
        return self._get_action_view_picking(
            self.picking_ids.filtered(lambda x: not x.show_in_purchase))
