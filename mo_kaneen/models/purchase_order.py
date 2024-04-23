from odoo import models, fields, api
from odoo.tools.translate import _
from .xml_rpc_request import connect
from odoo.exceptions import ValidationError, UserError


def get_standard_price(self, sku_shatha):
    url = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_url')
    username = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_username')
    db = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_dbname')
    password = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.xml_password')
    uid, models = connect(url, db, username, password)
    try:
        product_arr = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                                        [[['default_code', '=', sku_shatha]]], {'fields': ['standard_price']})
        shatha_standard_price = product_arr[-1]['standard_price']
    except IndexError:
        raise UserError(_(f'\'{self.product_id.name}\' is not found!'))
    except Exception:
        raise UserError(_('Credentials not correct'))
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

    def action_multi_confirm(self):
        for order in self.env['purchase.order'].browse(self.env.context.get('active_ids')).filtered(
                lambda o: o.state in ['draft', 'sent']):
            order.button_confirm()

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
        # self.order_line purchase.order.line(12014,)
        for line in self.order_line.filtered(lambda pol: pol.display_type not in ('line_section', 'line_note')):
            barcodes = []
            if line.product_id.barcode:
                barcodes.append(line.product_id.barcode)
            if line.product_id.barcode_ids:
                barcodes.extend(line.product_id.barcode_ids.mapped('name'))

            product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                        [[['default_code', '=', line.product_id.default_code]]],
                                        {'fields': ['name', 'id',
                                                    'product_variant_id']})  # ye chale ga hi nh product = []
            if not product:
                # try shata sku
                if line.product_id.sku_shatha:
                    product = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                [[['default_code', '=', line.product_id.sku_shatha]]],
                                                {'fields': ['name', 'id',
                                                            'product_variant_id']})  # [{'id': 32790, 'name': 'CHRISTIAN DIOR AMBRE NUIT (U) EDP 125 ml', 'product_variant_id': [32778, '[11990] CHRISTIAN DIOR AMBRE NUIT (U) EDP 125 ml']}]
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
                'price_unit': line.price_unit,
            }))
        create_data['order_line'] = products  # [(0, 0, {'product_id': 31206, 'product_uom_qty': 1.0})]
        create_data['client_order_ref'] = self.name  # purchase.order(3093,)
        try:
            models.execute_kw(db, uid, password, 'sale.order', 'create', [create_data])
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

    @api.onchange('product_qty', 'product_uom', 'company_id')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return
        if eval(self.product_id.sku_shatha):
            shatha_standard_price = get_standard_price(self, self.product_id.sku_shatha)
            self.price_unit = shatha_standard_price + 5

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line(product_id, product_qty, product_uom,
                                                                          company_id, supplier, po)
        if eval(product_id.sku_shatha):
            shatha_standard_price = get_standard_price(self, product_id.sku_shatha)
            res['price_unit'] = shatha_standard_price + 5
        return res


class BulkPurchaseExport(models.TransientModel):
    _name = 'bulk.purchase.export'

    def purchase_button_export(self):
        purchase_orders = self.env['purchase.order'].browse(self._context.get('active_ids', []))

        if len(purchase_orders) < 2:
            raise UserError(
                _('Please select atleast two purchase orders to perform '
                  'the Export Operation.'))

        # if any(not purchase_order.sale_order_count for purchase_order in purchase_orders):
        #     raise UserError(
        #         _(f'''Please select Purchase orders against which the sale order exists
        #         to perform the Export Operation.
        #         ***Unselect these orders {", ".join(purchase_order.name for purchase_order in purchase_orders if not purchase_order.sale_order_count)}'''))

        # if any(purchase_order._get_sale_orders().state != 'processing' for purchase_order in purchase_orders):
        #     raise UserError(
        #         _('Please select Purchase orders against which the sale order state is Processing state '
        #           'to perform the Export Operation.'))

        if any(purchase_order.send_status in ['sent'] for purchase_order in purchase_orders):
            raise UserError(
                _('Please unselect Purchase orders which are already exported '
                  'to perform the Export Operation.'))

        create_data = {}
        products = []
        url, db, username, password, responsible_partner_id = self.env['purchase.order'].get_rpc_params()

        uid, models = connect(url, db, username, password)

        shata_contact_id = self.env['ir.config_parameter'].sudo().get_param('mo_kaneen.shatha_remote_contact_id')

        partner = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[['id', '=', shata_contact_id]]],
                                    {'fields': ['name', 'id']})
        create_data['partner_id'] = partner[0]['id']

        if len(partner) > 1:
            raise ValidationError("Can not identify remote Kaneen buyer")

        product_list = []

        for obj in purchase_orders['order_line']:
            if obj['product_id'] not in product_list:
                product_list.append(obj['product_id'])

        for product in product_list:  # 1st product

            count = 0
            qty = 0

            for element in purchase_orders['order_line']:
                if product == element['product_id']:
                    qty += element['product_uom_qty']

            for purchase_line in purchase_orders['order_line']:
                if product == purchase_line['product_id']:
                    count += 1
                    if count == 1:

                        for line in purchase_line.filtered(
                                lambda pol: pol.display_type not in ('line_section', 'line_note')):
                            barcodes = []
                            if line.product_id.barcode:
                                barcodes.append(line.product_id.barcode)
                            if line.product_id.barcode_ids:
                                barcodes.extend(line.product_id.barcode_ids.mapped('name'))

                            product_template = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                                                 [[['default_code', '=',
                                                                    line.product_id.default_code]]],
                                                                 {'fields': ['name', 'id',
                                                                             'product_variant_id']})
                            if not product_template:
                                # try shata sku
                                if line.product_id.sku_shatha:
                                    product_template = models.execute_kw(db, uid, password, 'product.template',
                                                                         'search_read',
                                                                         [[['default_code', '=',
                                                                            line.product_id.sku_shatha]]],
                                                                         {'fields': ['name', 'id',
                                                                                     'product_variant_id']})  # [{'id': 32790, 'name': 'CHRISTIAN DIOR AMBRE NUIT (U) EDP 125 ml', 'product_variant_id': [32778, '[11990] CHRISTIAN DIOR AMBRE NUIT (U) EDP 125 ml']}]
                                if not product_template and barcodes:
                                    # try barcodes
                                    product_template = models.execute_kw(db, uid, password, 'product.template',
                                                                         'search_read',
                                                                         [[['barcode', 'in', barcodes]]],
                                                                         {'fields': ['name', 'id',
                                                                                     'product_variant_id']})
                                    if not product_template:
                                        continue

                            products.append((0, 0, {
                                'product_id': product_template[0]['product_variant_id'][0],
                                'product_uom_qty': qty,
                                'price_unit': line.price_unit,
                            }))

                        break

        create_data['order_line'] = products  # [(0, 0, {'product_id': 31206, 'product_uom_qty': 1.0})]
        create_data['client_order_ref'] = ', '.join(purchase_orders.mapped('name'))  # purchase.order(3093,)
        try:
            models.execute_kw(db, uid, password, 'sale.order', 'create', [create_data])
            purchase_orders.send_status = 'sent'
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
            template = self.env.ref('mo_kaneen.mail_template_user_send_to_shatha_error',
                                    raise_if_not_found=False)
            if template:
                email_values = {
                    'email_to': responsible_partner_id.email
                }
                template.send_mail(self.id, force_send=True, email_values=email_values)
