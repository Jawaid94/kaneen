from odoo import models, fields, api, _
from .xml_rpc_request import connect
from odoo.exceptions import ValidationError


def get_standard_price(self, sku_shatha):
    url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
    username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
    db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
    password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
    uid, models = connect(url, db, username, password)
    shatha_standard_price = \
    models.execute_kw(db, uid, password, 'product.product', 'search_read', [[['default_code', '=', sku_shatha]]],
                      {'fields': ['standard_price']})[-1]['standard_price']
    return shatha_standard_price


class Purchase(models.Model):
    _inherit = 'purchase.order'

    send_status = fields.Selection([('not_sent', 'Not Sent'),
                                    ('sent', 'Sent'),
                                    ('error', 'Error')], default='not_sent')
    message_send = fields.Boolean()
    visible_order_send_to_shatha = fields.Boolean('Send order to shatha visible?',
                                                  compute='_compute_visible_order_send_to_shatha')

    @api.depends('order_line')
    def _compute_visible_order_send_to_shatha(self):
        for purchase_order in self:
            purchase_order.visible_order_send_to_shatha = any(
                map(lambda x: x if x is False else eval(x), purchase_order.order_line.product_id.mapped('sku_shatha')))

    def get_rpc_params(self):
        url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
        db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
        username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
        password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
        responsible_partner = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.responsible_user_id')
        responsible_partner_id = self.env['res.users'].browse(int(responsible_partner)).partner_id
        return url, db, username, password, responsible_partner_id

    def send_order_to_shatha(self):
        create_data = {}
        products = []
        url, db, username, password, responsible_partner_id = self.get_rpc_params()

        uid, models = connect(url, db, username, password)

        shata_contact_id = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_remote_contact_id')

        partner = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[['id', '=', shata_contact_id]]],
                                    {'fields': ['name', 'id']})
        create_data['partner_id'] = partner[0]['id']

        if len(partner) > 1:
            raise ValidationError("Can not identify remote Kaneen buyer")

        for line in self.order_line.filtered(lambda pol: pol.display_type not in ('line_section', 'line_note')):
            barcodes = []
            if line.product_id.barcode:
                barcodes.append(line.product_id.barcode)
            if line.product_id.barcode_ids:
                barcodes.extend(line.product_id.barcode_ids.mapped('name'))

            product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                        [[['default_code', '=', line.product_id.default_code]]],
                                        {'fields': ['name', 'id', 'product_variant_id']})
            if not product:
                # try shata sku
                if line.product_id.sku_shatha:
                    product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                [[['default_code', '=', line.product_id.sku_shatha]]],
                                                {'fields': ['name', 'id', 'product_variant_id']})
                if not product and barcodes:
                    # try barcodes
                    product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                [[['barcode', 'in', barcodes]]],
                                                {'fields': ['name', 'id', 'product_variant_id']})
                    if not product:
                        continue

            products.append((0, 0, {
                'product_id': product[0]['product_variant_id'][0],
                'product_uom_qty': line.product_qty,
            }))
        create_data['order_line'] = products
        create_data['client_order_ref'] = self.name
        try:
            sale_order = models.execute_kw(db, uid, password, 'sale.order', 'create', [create_data])
            self.send_status = 'sent'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("Purchase order successfully exported"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except Exception as e:
            self.send_status = 'error'
            self.message_post(body=str(e))
            template = self.env.ref('mo_kaneen.mail_template_user_send_to_shatha_error', raise_if_not_found=False)
            if template:
                email_values = {
                    'email_to': responsible_partner_id.email
                }
                template.send_mail(self.id, force_send=True, email_values=email_values)

    def resend_order_to_shatha(self):
        url, db, username, password, responsible_partner_id = self.get_rpc_params()

        uid, models = connect(url, db, username, password)

        exist_purchase = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
                                           [[['client_order_ref', '=', self.name]]],
                                           {'fields': ['name', 'id', 'state'], 'limit': 1})

        if not exist_purchase or exist_purchase[0].get('state') == 'sale':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("Purchase order was confirmed in Shatha or not created"),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        try:
            for line in self.order_line:
                barcodes = []
                if line.product_id.barcode:
                    barcodes.append(line.product_id.barcode)
                if line.product_id.barcode_ids:
                    barcodes.extend(line.product_id.barcode_ids.mapped('name'))

                product = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                            [[['default_code', '=', line.product_id.default_code]]],
                                            {'fields': ['name', 'id']})
                if not product:
                    if line.product_id.sku_shatha:
                        product = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                                    [[['default_code', '=', line.product_id.sku_shatha]]],
                                                    {'fields': ['name', 'id']})
                    if not product and barcodes:
                        # try barcodes
                        product = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                                    [[['barcode', 'in', barcodes]]],
                                                    {'fields': ['name', 'id']})
                        if not product:
                            continue

                order_line = models.execute_kw(db, uid, password, 'sale.order.line', 'search_read',
                                               [[['order_id', '=', exist_purchase[0].get('id')],
                                                 ['product_id', '=', product[0].get('id')]]],
                                               {'fields': ['id'], 'limit': 1})
                if not order_line:
                    continue

                order_line = models.execute_kw(db, uid, password, 'sale.order.line', 'write',
                                               [[order_line[0].get('id')], {
                                                   'product_uom_qty': line.product_qty,
                                               }])
        except Exception as e:
            self.send_status = 'error'
            self.message_post(body=str(e))
            template = self.env.ref('mo_kaneen.mail_template_user_send_to_shatha_error', raise_if_not_found=False)
            if template:
                email_values = {
                    'email_to': responsible_partner_id.email
                }
                template.send_mail(self.id, force_send=True, email_values=email_values)
            return
        self.send_status = 'sent'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Purchase order successfully reexported"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def order_confirm_message(self):
        records = self.search([('message_send', '=', False)])
        url, db, username, password, responsible_partner_id = self.get_rpc_params()
        uid, models = connect(url, db, username, password)
        for record in records:
            order = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
                                      [[['client_order_ref', '=', record.name]]],
                                      {'fields': ['state', 'id']})
            if not order:
                continue
            if order[0]['state'] == 'sale':
                template = self.env.ref('mo_kaneen.mail_template_shata_order_confirm', raise_if_not_found=False)
                if template:
                    template.send_mail(record.id, force_send=True,
                                       email_values={'email_to': responsible_partner_id.email})
                record.message_send = True

    def send_order_to_shatha_cron(self):
        records = self.search([('send_status', '=', 'not_sent'), ('state', '=', 'purchase')])
        for record in records:
            record.send_order_to_shatha()

    def recount_price(self):
        for line in self.order_line:
            supplier = line.product_id.seller_ids.filtered(lambda x: x.name.name == 'Shatha AlKhaleej')
            if supplier and supplier.price != line.price_unit:
                line.update({
                    'price_unit': supplier.price
                })

    @api.depends('picking_ids')
    def _compute_incoming_picking_count(self):
        for order in self:
            sales = self.env['sale.order']
            sales_picking = self.env['stock.picking']
            if order.origin:
                sales_picking = sales.search(
                    [('name', 'in', order.origin.split(', '))]).picking_ids.filtered(lambda x: x.show_in_purchase)
            order.incoming_picking_count = len(order.picking_ids + sales_picking)

    def action_view_picking(self):
        sales = self.env['sale.order']
        sales_picking = self.env['stock.picking']
        if self.origin:
            sales_picking = sales.search(
                [('name', 'in', self.origin.split(', '))]).picking_ids.filtered(lambda x: x.show_in_purchase)
        return self._get_action_view_picking(self.picking_ids + sales_picking)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line(product_id, product_qty, product_uom,
                                                                          company_id, supplier, po)
        if eval(product_id.sku_shatha):
            shatha_standard_price = get_standard_price(self, product_id.sku_shatha)
            res['price_unit'] = shatha_standard_price + 5
        return res