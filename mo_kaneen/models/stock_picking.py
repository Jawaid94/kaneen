from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.tools import html2plaintext, is_html_empty


class Picking(models.Model):
    _inherit = 'stock.picking'

    show_in_sale = fields.Boolean()
    show_in_purchase = fields.Boolean()

    # jawaid 28/8/2023
    # def _check_damaged(self):
    #     for picking in self.filtered(lambda x: x.group_id):
    #         sale_order_id = picking.group_id.sale_id
    #         if not sale_order_id:
    #             continue
    #
    #         if picking.picking_type_code != 'incoming' and picking.picking_type_id.name != 'Returns':
    #             continue
    #
    #         if any(line.has_damaged_item for line in picking.move_ids_without_package):
    #             state = 'damaged_item'
    #         else:
    #             state = 'item_returned'
    #
    #         sale_order_id.write({
    #             'state': state
    #         })
    #
    #         if not sale_order_id.invoice_ids or state == "item_returned":
    #             continue
    #
    #         delivery_product = sale_order_id.order_line.filtered(
    #             lambda x: x.product_id.detailed_type == 'service' and x.product_id.default_code == 'MAGENTO_SHIP')
    #         if not delivery_product:
    #             continue
    #
    #         create_refund_delivery = True
    #         refund = sale_order_id.invoice_ids.filtered(lambda x: x.move_type == 'out_refund' and x.state != 'cancel')
    #         if refund:
    #             delivery = refund.invoice_line_ids.filtered(
    #                 lambda x: x.product_id.detailed_type == 'service' and x.product_id.default_code == 'MAGENTO_SHIP')
    #             if delivery:
    #                 create_refund_delivery = False
    #         else:
    #             create_refund_delivery = True
    #
    #         reversal_wizard = self.env['account.move.reversal'].create({
    #             'move_ids': [(6, 0, sale_order_id.invoice_ids.ids)],
    #             'date_mode': 'custom',
    #             'refund_method': 'refund',
    #             'journal_id': sale_order_id.invoice_ids[0].journal_id.id,
    #             'company_id': sale_order_id.company_id.id
    #         })
    #         reversal_move = reversal_wizard.reverse_moves()
    #         refund = self.env['account.move'].browse(reversal_move.get('res_id', False))
    #
    #         first_invoice = sale_order_id.invoice_ids.filtered(
    #             lambda x: x.move_type == 'out_invoice' and x.state != 'cancel')[-1]
    #
    #         invoiced_delivery = first_invoice.invoice_line_ids.filtered(
    #             lambda x: x.product_id.detailed_type == 'service' and x.product_id.default_code == 'MAGENTO_SHIP')
    #
    #         products = self.move_lines.mapped('product_id') | invoiced_delivery.product_id
    #
    #         account_line = refund.invoice_line_ids.filtered(
    #             lambda x: x.product_id.id not in products.ids)
    #         refund.write({
    #             "invoice_line_ids": [(2, i) for i in account_line.ids],
    #             "return_picking_id": self.id
    #         })
    #         for line in self.move_lines:
    #             refund.invoice_line_ids.filtered(
    #                 lambda x: x.product_id.id == line.product_id.id).with_context(
    #                 check_move_validity=False).write({
    #                 'quantity': line.quantity_done
    #             })
    #
    #         if create_refund_delivery:
    #             refund.invoice_line_ids.filtered(
    #                 lambda x: x.product_id == invoiced_delivery).with_context(
    #                 check_move_validity=False).write({
    #                 'quantity': 1
    #             })
    #
    #         sale_order_id._sale_order_payment_status()
    # jawaid 28/8/2023

    # if not create_refund_delivery:
    #     continue
    #
    # first_invoice = sale_order_id.invoice_ids.filtered(
    #     lambda x: x.move_type == 'out_invoice' and x.state != 'cancel')[-1]
    #
    # invoiced_delivery = first_invoice.invoice_line_ids.filtered(
    #     lambda x: x.product_id.detailed_type == 'service' and x.product_id.default_code == 'MAGENTO_SHIP')
    # if not invoiced_delivery:
    #     continue
    #
    # invoiced_delivery = invoiced_delivery[0]
    #
    # # not_done_refund = sale_order_id.invoice_ids[0]
    #
    # refund_delivery_data = invoiced_delivery.copy_data({
    #     'move_id': refund[0].id
    # })[0]
    #
    # amount_currency = -refund_delivery_data.get('amount_currency', 0.0)
    # balance = refund_delivery_data['credit'] - refund_delivery_data['debit']
    # if 'tax_tag_invert' in refund_delivery_data and not first_invoice.tax_cash_basis_origin_move_id:
    #     del refund_delivery_data['tax_tag_invert']
    #
    # refund_delivery_data.update({
    #     'amount_currency': amount_currency,
    #     'debit': balance > 0.0 and balance or 0.0,
    #     'credit': balance < 0.0 and -balance or 0.0,
    # })
    #
    # def compute_tax_repartition_lines_mapping(move_vals):
    #     ''' Computes and returns a mapping between the current repartition lines to the new expected one.
    #     :param move_vals:   The newly created invoice as a python dictionary to be passed to the 'create' method.
    #     :return:            A map invoice_repartition_line => refund_repartition_line.
    #     '''
    #     # invoice_repartition_line => refund_repartition_line
    #     mapping = {}
    #
    #     if move_vals.get('tax_line_id'):
    #         # Tax line.
    #         tax_ids = [move_vals['tax_line_id']]
    #     elif move_vals.get('tax_ids') and move_vals['tax_ids'][0][2]:
    #         # Base line.
    #         tax_ids = move_vals['tax_ids'][0][2]
    #
    #     for tax in self.env['account.tax'].browse(tax_ids).flatten_taxes_hierarchy():
    #         for inv_rep_line, ref_rep_line in zip(tax.invoice_repartition_line_ids,
    #                                               tax.refund_repartition_line_ids):
    #             mapping[inv_rep_line] = ref_rep_line
    #
    #     return mapping
    #
    # tax_repartition_lines_mapping = compute_tax_repartition_lines_mapping(refund_delivery_data)
    #
    # # ==== Map tax repartition lines ====
    # if refund_delivery_data.get('tax_repartition_line_id'):
    #     # Tax line.
    #     invoice_repartition_line = self.env['account.tax.repartition.line'].browse(
    #         refund_delivery_data['tax_repartition_line_id'])
    #     if invoice_repartition_line not in tax_repartition_lines_mapping:
    #         raise UserError(
    #             _("It seems that the taxes have been modified since the creation of the journal entry. You should create the credit note manually instead."))
    #     refund_repartition_line = tax_repartition_lines_mapping[invoice_repartition_line]
    #
    #     # Find the right account.
    #     account_id = self.env['account.move.line']._get_default_tax_account(refund_repartition_line).id
    #     if not account_id:
    #         if not invoice_repartition_line.account_id:
    #             # Keep the current account as the current one comes from the base line.
    #             account_id = refund_delivery_data['account_id']
    #         else:
    #             tax = invoice_repartition_line.invoice_tax_id
    #             base_line = self.line_ids.filtered(lambda line: tax in line.tax_ids.flatten_taxes_hierarchy())[
    #                 0]
    #             account_id = base_line.account_id.id
    #
    #     tags = refund_repartition_line.tag_ids
    #     if refund_delivery_data.get('tax_ids'):
    #         subsequent_taxes = self.env['account.tax'].browse(refund_delivery_data['tax_ids'][0][2])
    #         tags += subsequent_taxes.refund_repartition_line_ids.filtered(
    #             lambda x: x.repartition_type == 'base').tag_ids
    #
    #     refund_delivery_data.update({
    #         'tax_repartition_line_id': refund_repartition_line.id,
    #         'account_id': account_id,
    #         'tax_tag_ids': [(6, 0, tags.ids)],
    #     })
    # elif refund_delivery_data.get('tax_ids') and refund_delivery_data['tax_ids'][0][2]:
    #     # Base line.
    #     taxes = self.env['account.tax'].browse(refund_delivery_data['tax_ids'][0][2]).flatten_taxes_hierarchy()
    #     invoice_repartition_lines = taxes \
    #         .mapped('invoice_repartition_line_ids') \
    #         .filtered(lambda line: line.repartition_type == 'base')
    #     refund_repartition_lines = invoice_repartition_lines \
    #         .mapped(lambda line: tax_repartition_lines_mapping[line])
    #
    #     refund_delivery_data['tax_tag_ids'] = [(6, 0, refund_repartition_lines.mapped('tag_ids').ids)]

    # new_line = self.env['account.move.line'].with_context(
    #     check_move_validity=False).create(refund_delivery_data)

    def _update_reserve_from_customer(self):
        for picking in self:
            if picking.picking_type_code != 'incoming' and picking.picking_type_id.name != 'Returns':
                continue

            for line in picking.move_line_ids_without_package.filtered(lambda x: x.state == 'assigned'):
                self.env['stock.quant']._update_reserved_quantity(line.product_id, line.location_dest_id, line.qty_done,
                                                                  line.lot_id, line.package_id, line.owner_id,
                                                                  strict=True)

    # jawaid 30/8/2023 all comment
    # # jawaid 28/8/2023
    # def _action_done(self):
    #     # self._check_damaged()
    #
    #     super(Picking, self)._action_done()
    #     for picking in self:
    #         sale_order = picking.sale_id
    #         if sale_order:
    #             if sale_order.state in ['damaged_item', 'item_returned']:
    #                 continue
    #
    #             pickings_pick = sale_order.picking_ids.filtered(lambda x: x.picking_type_code == 'internal' and x.state not in ['cancel'])
    #             pickings_out = sale_order.picking_ids.filtered(lambda x: x.picking_type_code == 'outgoing' and x.state not in ['cancel'])
    #             # jawaid 29/8/2023
    #             # payload = {
    #             #     "entity": {
    #             #         "entity_id": sale_order.magento_order_id,
    #             #         "status": "shipped",
    #             #         "status_histories": [
    #             #             {
    #             #                 "comment": "Order status updated by Odoo",
    #             #                 "entity_name": "order",
    #             #                 "is_customer_notified": 0,
    #             #                 "is_visible_on_front": 0,
    #             #                 "parent_id": sale_order.magento_order_id,
    #             #                 "status": "shipped"
    #             #             }
    #             #         ]
    #             #     }
    #             # }
    #             # jawaid 29/8/2023
    #             if all(picking.state == 'done' for picking in pickings_out) and sale_order.state != 'shipped':
    #                 sale_order.sudo().write({
    #                     'state': 'shipped'
    #                 })
    #                 # request = req(self.magento_instance_id, '/all/V1/orders', 'POST', payload, is_raise=True) jawaid 29/8/2023
    #                 continue
    #             if all(picking.state == 'done' for picking in pickings_pick) and sale_order.state not in \
    #                     ['shipped', 'ready_to_ship', 'item_returned']:
    #                 sale_order.sudo().write({
    #                     'state': 'ready_to_ship'
    #                 })
    #                 # jawaid 29/8/2023
    #                 # payload['entity'].update(
    #                 #     {
    #                 #         "status": "ready_to_ship",
    #                 #     })
    #                 # payload['entity']['status_histories'].update(
    #                 #     {
    #                 #         "status": "ready_to_ship",
    #                 #     })
    #                 # request = req(self.magento_instance_id, '/all/V1/orders', 'POST', payload, is_raise=True) jawaid 29/8/2023
    #
    # #     jawaid 28/8/2023
    # jawaid 30/8/2023 all comment

    def _check_return(self):
        pickings = self.filtered(lambda x: x.picking_type_code == 'incoming' and x.picking_type_id.name == 'Returns')
        return pickings

    # jawaid 28/8/2023
    # def _pre_action_done_hook(self):
    #     res = super()._pre_action_done_hook()
    #     if res is not True:
    #         return res
    #
    #     if not self.env.context.get('skip_return_validation'):
    #         pickings_to_validate = self._check_return()
    #         if pickings_to_validate:
    #             return pickings_to_validate._action_generate_return_validation_wizard()
    #
    #     return True
    #     jawaid 28/8/2023

    def _action_generate_return_validation_wizard(self):
        view = self.env.ref('mo_kaneen.return_validation_wizard_form')
        return {
            'name': _('Return Validation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'return.validation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_picking_id=self.id, active_id=self.id, active_ids=self.ids,
                            active_model="stock.picking"),
        }

    def _get_stock_barcode_data(self):
        # Avoid to get the products full name because code and name are separate in the barcode app.
        self = self.with_context(display_default_code=False)
        move_lines = self.move_line_ids
        lots = move_lines.lot_id
        owners = move_lines.owner_id
        # Fetch all implied products in `self` and adds last used products to avoid additional rpc.
        products = move_lines.product_id
        packagings = products.packaging_ids

        uoms = products.uom_id | move_lines.product_uom_id
        # If UoM setting is active, fetch all UoM's data.
        if self.env.user.has_group('uom.group_uom'):
            uoms |= self.env['uom.uom'].search([])

        # Fetch `stock.quant.package` and `stock.package.type` if group_tracking_lot.
        packages = self.env['stock.quant.package']
        package_types = self.env['stock.package.type']
        if self.env.user.has_group('stock.group_tracking_lot'):
            packages |= move_lines.package_id | move_lines.result_package_id
            packages |= self.env['stock.quant.package']._get_usable_packages()
            package_types = package_types.search([])

        # Fetch `stock.location`
        source_locations = self.env['stock.location'].search([('id', 'child_of', self.location_id.ids)])
        destination_locations = self.env['stock.location'].search([('id', 'child_of', self.location_dest_id.ids)])
        locations = move_lines.location_id | move_lines.location_dest_id | source_locations | destination_locations

        result_products = []
        products = products.read(products._get_fields_stock_barcode(), load=False)
        for product in products:
            barcodes = self.env['product.barcode.multi'].browse(product['barcode_ids'])
            product.update({
                'barcodes': barcodes.mapped("name")
            })
            result_products.append(product)

        data = {
            "records": {
                "stock.picking": self.read(self._get_fields_stock_barcode(), load=False),
                "stock.move.line": move_lines.read(move_lines._get_fields_stock_barcode(), load=False),
                "product.product": result_products,
                "product.packaging": packagings.read(packagings._get_fields_stock_barcode(), load=False),
                "res.partner": owners.read(owners._get_fields_stock_barcode(), load=False),
                "stock.location": locations.read(locations._get_fields_stock_barcode(), load=False),
                "stock.package.type": package_types.read(package_types._get_fields_stock_barcode(), False),
                "stock.quant.package": packages.read(packages._get_fields_stock_barcode(), load=False),
                "stock.production.lot": lots.read(lots._get_fields_stock_barcode(), load=False),
                "uom.uom": uoms.read(uoms._get_fields_stock_barcode(), load=False),
            },
            "nomenclature_id": [self.env.company.nomenclature_id.id],
            "source_location_ids": source_locations.ids,
            "destination_locations_ids": destination_locations.ids,
        }
        # Extracts pickings' note if it's empty HTML.
        for picking in data['records']['stock.picking']:
            picking['note'] = False if is_html_empty(picking['note']) else html2plaintext(picking['note'])
        return data

    @api.model
    def filter_on_product(self, barcode):
        product = self.env['product.product'].search_read([('barcode', '=', barcode)], ['id'], limit=1)
        if not product:
            bc = self.env['product.barcode.multi'].search_read([('name', '=', barcode)], ['id', 'product_id'],
                                                               limit=1)
            if bc and bc[0]['product_id']:
                product = self.env['product.product'].search_read([('id', '=', bc[0]['product_id'][0])], ['id'],
                                                                  limit=1)

        if product:
            product_id = product[0]['id']
            picking_type = self.env['stock.picking.type'].search_read(
                [('id', '=', self.env.context.get('active_id'))],
                ['name'],
            )[0]
            if not self.search_count([
                ('product_id', '=', product_id),
                ('picking_type_id', '=', picking_type['id']),
                ('state', 'not in', ['cancel', 'done', 'draft']),
            ]):
                return {'warning': {
                    'title': _("No %s ready for this product", picking_type['name']),
                }}
            action = self.env['ir.actions.actions']._for_xml_id('stock_barcode.stock_picking_action_kanban')
            action['context'] = dict(self.env.context)
            action['context']['search_default_product_id'] = product_id
            return {'action': action}

        return {'warning': {
            'title': _("No product found for barcode %s", barcode),
            'message': _("Scan a product to filter the transfers."),
        }}


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super()._prepare_move_default_values(return_line, new_picking)
        if return_line.return_comment:
            vals['return_comments'] = return_line.return_comment
        return vals


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    return_comment = fields.Char()
