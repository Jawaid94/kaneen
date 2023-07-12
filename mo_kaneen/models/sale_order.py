from odoo import models, fields, api
from odoo.tools import float_is_zero, float_compare, float_round

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

    def _get_invoiceable_lines(self,  final=False):
        res = super()._get_invoiceable_lines(final)
        res = res.filtered(lambda x: x.price_unit > 0)
        return res


# class SaleLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     product_quality = fields.Selection(selection=quality_items, string="Product quality")
#
#     product_quality_comment_id = fields.Many2many('mo.product.quality.comment', string="Product quality comment")
#
#
# class SaleReport(models.Model):
#     _inherit = "sale.report"
#
#     product_quality = fields.Selection(selection=quality_items, string="Product quality")
#
#     def _select_sale(self, fields=None):
#         if not fields:
#             fields = {}
#         select_ = """
#             coalesce(min(l.id), -s.id) as id,
#             l.product_id as product_id,
#             t.uom_id as product_uom,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as product_uom_qty,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_delivered / u.factor * u2.factor) ELSE 0 END as qty_delivered,
#             CASE WHEN l.product_id IS NOT NULL THEN SUM((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) ELSE 0 END as qty_to_deliver,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_invoiced / u.factor * u2.factor) ELSE 0 END as qty_invoiced,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.qty_to_invoice / u.factor * u2.factor) ELSE 0 END as qty_to_invoice,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as price_total,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as price_subtotal,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as untaxed_amount_to_invoice,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) ELSE 0 END as untaxed_amount_invoiced,
#             count(*) as nbr,
#             s.name as name,
#             s.date_order as date,
#             s.state as state,
#             s.partner_id as partner_id,
#             s.user_id as user_id,
#             s.company_id as company_id,
#             s.campaign_id as campaign_id,
#             s.medium_id as medium_id,
#             s.source_id as source_id,
#             extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
#             t.categ_id as categ_id,
#             s.pricelist_id as pricelist_id,
#             s.analytic_account_id as analytic_account_id,
#             s.team_id as team_id,
#             p.product_tmpl_id,
#             partner.country_id as country_id,
#             partner.industry_id as industry_id,
#             partner.commercial_partner_id as commercial_partner_id,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(p.weight * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as weight,
#             CASE WHEN l.product_id IS NOT NULL THEN sum(p.volume * l.product_uom_qty / u.factor * u2.factor) ELSE 0 END as volume,
#             l.discount as discount,
#             CASE WHEN l.product_id IS NOT NULL THEN sum((l.price_unit * l.product_uom_qty * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END))ELSE 0 END as discount_amount,
#             s.id as order_id,
#             l.product_quality as product_quality
#         """
#
#         for field in fields.values():
#             select_ += field
#         return select_
#
#     def _group_by_sale(self, groupby=''):
#         groupby_ = """
#             l.product_id,
#             l.order_id,
#             t.uom_id,
#             t.categ_id,
#             s.name,
#             s.date_order,
#             s.partner_id,
#             s.user_id,
#             s.state,
#             s.company_id,
#             s.campaign_id,
#             s.medium_id,
#             s.source_id,
#             s.pricelist_id,
#             s.analytic_account_id,
#             s.team_id,
#             p.product_tmpl_id,
#             partner.country_id,
#             partner.industry_id,
#             partner.commercial_partner_id,
#             l.discount,
#             s.id %s,
#             l.product_quality
#         """ % (groupby)
#         return groupby_
